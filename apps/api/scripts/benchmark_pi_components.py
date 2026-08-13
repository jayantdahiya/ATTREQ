#!/usr/bin/env python3
"""BR-04 Raspberry Pi component benchmark harness.

The four benchmarks are deliberately independent:

* ``fashionclip`` measures ATTREQ's in-process FashionCLIP service;
* ``weaviate`` measures manual-vector insert/query overhead without a vectorizer;
* ``text2vec`` measures the transformer's HTTP inference endpoint directly;
* ``reranker`` measures ATTREQ's real, remote LLM reranker against synthetic cases.

Results are JSON and never contain environment variables, authorization headers,
HTTP response bodies, model rationales, or source image paths.  A probe spec may
contain credentials, so the harness refuses one that is readable by group/other.
See ``docs/08-beta-readiness/02-br04-pi-benchmark-runbook.md``.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import math
import os
import platform
import random
import resource
import statistics
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

if TYPE_CHECKING:
    from collections.abc import Callable
    from uuid import UUID

SCHEMA_VERSION = 1


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return round(ordered[lower], 3)
    value = ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)
    return round(value, 3)


def _latency_summary(values: list[float]) -> dict[str, float | int | None]:
    return {
        "count": len(values),
        "min_ms": round(min(values), 3) if values else None,
        "mean_ms": round(statistics.fmean(values), 3) if values else None,
        "p50_ms": _percentile(values, 0.50),
        "p95_ms": _percentile(values, 0.95),
        "max_ms": round(max(values), 3) if values else None,
    }


def _read_meminfo() -> dict[str, int | None]:
    values: dict[str, int] = {}
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            key, raw = line.split(":", 1)
            values[key] = int(raw.strip().split()[0])
    except (OSError, ValueError, IndexError):
        return {"total_mib": None, "available_mib": None}
    return {
        "total_mib": round(values.get("MemTotal", 0) / 1024),
        "available_mib": round(values.get("MemAvailable", 0) / 1024),
    }


def _process_rss_mib() -> float | None:
    try:
        for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
            if line.startswith("VmRSS:"):
                return round(int(line.split()[1]) / 1024, 3)
    except (OSError, ValueError, IndexError):
        pass
    # macOS reports bytes; Linux reports KiB.
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if not peak:
        return None
    divisor = 1024 * 1024 if sys.platform == "darwin" else 1024
    return round(peak / divisor, 3)


def _host_snapshot() -> dict[str, Any]:
    try:
        load = [round(value, 3) for value in os.getloadavg()]
    except OSError:
        load = []
    return {
        "architecture": platform.machine(),
        "system": platform.system(),
        "release": platform.release(),
        "cpu_count": os.cpu_count(),
        "load_average_1m_5m_15m": load,
        "memory": _read_meminfo(),
        "process_rss_mib": _process_rss_mib(),
        "temperature_c": _temperature_c(),
    }


def _temperature_c() -> float | None:
    try:
        raw = Path("/sys/class/thermal/thermal_zone0/temp").read_text(encoding="utf-8")
        return round(float(raw.strip()) / 1000, 3)
    except (OSError, ValueError):
        return None


def _cpu_counters() -> tuple[int, int] | None:
    try:
        fields = Path("/proc/stat").read_text(encoding="utf-8").splitlines()[0].split()[1:]
        values = [int(field) for field in fields]
    except (OSError, ValueError, IndexError):
        return None
    idle = values[3] + (values[4] if len(values) > 4 else 0)
    return idle, sum(values)


@dataclass
class HostStatsSampler:
    interval_seconds: float = 0.5
    samples: list[dict[str, float]] = field(default_factory=list)
    _stop: threading.Event = field(default_factory=threading.Event)
    _thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> dict[str, Any]:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=max(2.0, self.interval_seconds * 3))
        cpus = [sample["cpu_percent"] for sample in self.samples if "cpu_percent" in sample]
        available = [
            sample["available_mib"] for sample in self.samples if "available_mib" in sample
        ]
        temperatures = [
            sample["temperature_c"] for sample in self.samples if "temperature_c" in sample
        ]
        return {
            "sample_count": len(self.samples),
            "cpu_percent_peak": round(max(cpus), 3) if cpus else None,
            "cpu_percent_mean": round(statistics.fmean(cpus), 3) if cpus else None,
            "memory_available_mib_min": round(min(available), 3) if available else None,
            "temperature_c_peak": round(max(temperatures), 3) if temperatures else None,
        }

    def _run(self) -> None:
        previous = _cpu_counters()
        while not self._stop.wait(self.interval_seconds):
            sample: dict[str, float] = {}
            current = _cpu_counters()
            if previous is not None and current is not None:
                idle_delta = current[0] - previous[0]
                total_delta = current[1] - previous[1]
                if total_delta > 0:
                    sample["cpu_percent"] = 100 * (1 - idle_delta / total_delta)
            previous = current
            memory = _read_meminfo().get("available_mib")
            if memory is not None:
                sample["available_mib"] = float(memory)
            temperature = _temperature_c()
            if temperature is not None:
                sample["temperature_c"] = temperature
            if sample:
                self.samples.append(sample)


def _parse_size_mib(raw: str) -> float | None:
    raw = raw.strip()
    units = {
        "B": 1 / (1024 * 1024),
        "KiB": 1 / 1024,
        "MiB": 1,
        "GiB": 1024,
        "kB": 1000 / (1024 * 1024),
        "MB": 1_000_000 / (1024 * 1024),
        "GB": 1_000_000_000 / (1024 * 1024),
    }
    for unit in sorted(units, key=len, reverse=True):
        if raw.endswith(unit):
            try:
                return float(raw[: -len(unit)]) * units[unit]
            except ValueError:
                return None
    return None


@dataclass
class DockerStatsSampler:
    containers: list[str]
    interval_seconds: float = 0.5
    samples: dict[str, list[dict[str, float]]] = field(default_factory=dict)
    _stop: threading.Event = field(default_factory=threading.Event)
    _thread: threading.Thread | None = None

    def start(self) -> None:
        if not self.containers:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> dict[str, Any]:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=max(2.0, self.interval_seconds * 3))
        summary: dict[str, Any] = {}
        for name, samples in self.samples.items():
            cpus = [sample["cpu_percent"] for sample in samples]
            memory = [sample["memory_mib"] for sample in samples]
            summary[name] = {
                "sample_count": len(samples),
                "cpu_percent_peak": round(max(cpus), 3) if cpus else None,
                "cpu_percent_mean": round(statistics.fmean(cpus), 3) if cpus else None,
                "memory_mib_peak": round(max(memory), 3) if memory else None,
                "memory_mib_mean": round(statistics.fmean(memory), 3) if memory else None,
            }
        return summary

    def _run(self) -> None:
        while not self._stop.is_set():
            for container in self.containers:
                try:
                    completed = subprocess.run(
                        [
                            "docker",
                            "stats",
                            "--no-stream",
                            "--format",
                            "{{json .}}",
                            container,
                        ],
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    payload = json.loads(completed.stdout.strip())
                    memory_raw = str(payload.get("MemUsage", "")).split("/", 1)[0].strip()
                    cpu = float(str(payload.get("CPUPerc", "0")).rstrip("%"))
                    memory = _parse_size_mib(memory_raw)
                    if memory is not None:
                        self.samples.setdefault(container, []).append(
                            {"cpu_percent": cpu, "memory_mib": memory}
                        )
                except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError):
                    # Missing/finished containers are represented by zero samples.
                    self.samples.setdefault(container, [])
            self._stop.wait(self.interval_seconds)


@dataclass(frozen=True)
class Probe:
    name: str
    url: str
    method: str
    headers: dict[str, str]
    body: bytes | None
    timeout_seconds: float


@dataclass
class ProbeSampler:
    probes: list[Probe]
    interval_seconds: float = 0.5
    results: dict[str, list[tuple[float, int | None]]] = field(default_factory=dict)
    _stop: threading.Event = field(default_factory=threading.Event)
    _thread: threading.Thread | None = None

    def start(self) -> None:
        if not self.probes:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> dict[str, Any]:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=10)
        summary: dict[str, Any] = {}
        for probe in self.probes:
            rows = self.results.get(probe.name, [])
            latencies = [latency for latency, _status in rows]
            statuses: dict[str, int] = {}
            for _latency, status in rows:
                key = str(status) if status is not None else "transport_error"
                statuses[key] = statuses.get(key, 0) + 1
            summary[probe.name] = {
                "latency": _latency_summary(latencies),
                "statuses": statuses,
            }
        return summary

    def _run(self) -> None:
        while not self._stop.is_set():
            for probe in self.probes:
                started = time.perf_counter()
                status: int | None = None
                try:
                    request = urllib.request.Request(
                        probe.url,
                        data=probe.body,
                        headers=probe.headers,
                        method=probe.method,
                    )
                    with urllib.request.urlopen(request, timeout=probe.timeout_seconds) as response:
                        status = response.status
                        response.read(1)
                except urllib.error.HTTPError as error:
                    status = error.code
                except (OSError, urllib.error.URLError):
                    status = None
                elapsed_ms = (time.perf_counter() - started) * 1000
                self.results.setdefault(probe.name, []).append((elapsed_ms, status))
            self._stop.wait(self.interval_seconds)


def _load_probe_spec(path: str | None) -> list[Probe]:
    if not path:
        return []
    spec_path = Path(path)
    mode = spec_path.stat().st_mode & 0o777
    if mode & 0o077:
        raise PermissionError("probe spec must not be readable or writable by group/other")
    payload = json.loads(spec_path.read_text(encoding="utf-8"))
    probes = []
    for row in payload.get("probes", []):
        method = str(row.get("method", "GET")).upper()
        body = row.get("json_body")
        encoded = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {str(key): str(value) for key, value in row.get("headers", {}).items()}
        if encoded is not None:
            headers.setdefault("Content-Type", "application/json")
        probes.append(
            Probe(
                name=str(row["name"]),
                url=str(row["url"]),
                method=method,
                headers=headers,
                body=encoded,
                timeout_seconds=float(row.get("timeout_seconds", 10)),
            )
        )
    return probes


def _run_measured(
    args: argparse.Namespace, workload: Callable[[], dict[str, Any]]
) -> dict[str, Any]:
    probes = ProbeSampler(_load_probe_spec(args.probe_spec), args.sample_interval)
    containers = DockerStatsSampler(args.docker_container, args.sample_interval)
    host_stats = HostStatsSampler(args.sample_interval)
    before = _host_snapshot()
    started = time.perf_counter()
    probes.start()
    containers.start()
    host_stats.start()
    try:
        measurements = workload()
        status = "pass"
        error_type = None
    except Exception as error:  # top-level result must be machine-readable
        measurements = {}
        status = "fail"
        error_type = type(error).__name__
    elapsed_ms = (time.perf_counter() - started) * 1000
    result = {
        "schema_version": SCHEMA_VERSION,
        "component": args.component,
        "run_id": str(uuid4()),
        "recorded_at": _utc_now(),
        "status": status,
        "error_type": error_type,
        "elapsed_ms": round(elapsed_ms, 3),
        "host_before": before,
        "host_after": _host_snapshot(),
        "host_stats": host_stats.stop(),
        "docker_stats": containers.stop(),
        "api_probes": probes.stop(),
        "measurements": measurements,
    }
    return result


def _fashionclip(args: argparse.Namespace) -> dict[str, Any]:
    from attreq_api.services.ai.fashion_embeddings import EMBEDDING_DIM, FashionEmbeddingsService

    image_paths = [Path(path) for path in args.image]
    if not image_paths or any(not path.is_file() for path in image_paths):
        raise FileNotFoundError

    service = FashionEmbeddingsService()
    started = time.perf_counter()
    if not service.is_available():
        raise RuntimeError
    cold_load_ms = (time.perf_counter() - started) * 1000

    latencies: list[float] = []
    dimensions: list[int] = []
    for iteration in range(args.iterations):
        image_path = image_paths[iteration % len(image_paths)]
        started = time.perf_counter()
        vector = service.embed_image(str(image_path))
        latencies.append((time.perf_counter() - started) * 1000)
        if vector is None:
            raise RuntimeError
        dimensions.append(len(vector))

    concurrent_paths = [image_paths[index % len(image_paths)] for index in range(5)]

    def embed(path: Path) -> tuple[float, int | None]:
        call_started = time.perf_counter()
        vector = service.embed_image(str(path))
        return (time.perf_counter() - call_started) * 1000, len(vector) if vector else None

    concurrent_started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=5) as executor:
        concurrent_results = list(executor.map(embed, concurrent_paths))
    concurrent_wall_ms = (time.perf_counter() - concurrent_started) * 1000
    if any(dimension != EMBEDDING_DIM for _latency, dimension in concurrent_results):
        raise RuntimeError

    return {
        "model": "patrickjohncyh/fashion-clip",
        "device": service._device,
        "image_count": len(image_paths),
        "cold_model_load_ms": round(cold_load_ms, 3),
        "single_image_latency": _latency_summary(latencies),
        "five_job_wall_ms": round(concurrent_wall_ms, 3),
        "five_job_individual_latency": _latency_summary(
            [latency for latency, _dimension in concurrent_results]
        ),
        "all_vectors_valid": all(dimension == EMBEDDING_DIM for dimension in dimensions),
    }


def _weaviate(args: argparse.Namespace) -> dict[str, Any]:
    import weaviate
    from weaviate.classes.config import Configure, DataType, Property, VectorDistances
    from weaviate.classes.query import Filter, MetadataQuery

    collection_name = f"Br04Vector{uuid4().hex}"
    user_id = uuid4()
    randomizer = random.Random(args.seed)
    vectors: list[list[float]] = []
    for _index in range(args.objects):
        vector = [randomizer.uniform(-1, 1) for _dimension in range(args.dimension)]
        norm = math.sqrt(sum(value * value for value in vector))
        vectors.append([value / norm for value in vector])

    client = weaviate.connect_to_local(
        host=args.host,
        port=args.http_port,
        grpc_port=args.grpc_port,
    )
    insert_latencies: list[float] = []
    query_latencies: list[float] = []
    try:
        client.collections.create(
            name=collection_name,
            vectorizer_config=Configure.Vectorizer.none(),
            vector_index_config=Configure.VectorIndex.hnsw(distance_metric=VectorDistances.COSINE),
            properties=[
                Property(name="itemId", data_type=DataType.TEXT),
                Property(name="userId", data_type=DataType.TEXT),
            ],
        )
        collection = client.collections.get(collection_name)
        item_ids: list[UUID] = []
        for vector in vectors:
            item_id = uuid4()
            item_ids.append(item_id)
            started = time.perf_counter()
            collection.data.insert(
                properties={"itemId": str(item_id), "userId": str(user_id)},
                vector=vector,
            )
            insert_latencies.append((time.perf_counter() - started) * 1000)

        result_counts: list[int] = []
        for index in range(args.queries):
            started = time.perf_counter()
            response = collection.query.near_vector(
                near_vector=vectors[index % len(vectors)],
                limit=min(5, args.objects),
                filters=Filter.by_property("userId").equal(str(user_id)),
                return_metadata=MetadataQuery(distance=True),
            )
            query_latencies.append((time.perf_counter() - started) * 1000)
            result_counts.append(len(response.objects))
        return {
            "objects": args.objects,
            "dimension": args.dimension,
            "insert_latency": _latency_summary(insert_latencies),
            "query_latency": _latency_summary(query_latencies),
            "all_queries_returned_results": all(count > 0 for count in result_counts),
        }
    finally:
        try:
            client.collections.delete(collection_name)
        finally:
            client.close()


def _extract_vector(payload: Any) -> list[float] | None:
    if (
        isinstance(payload, list)
        and payload
        and all(isinstance(item, (int, float)) for item in payload)
    ):
        return [float(item) for item in payload]
    if isinstance(payload, dict):
        for key in ("vector", "vectors", "embeddings"):
            if key in payload:
                vector = _extract_vector(payload[key])
                if vector:
                    return vector
        for value in payload.values():
            vector = _extract_vector(value)
            if vector:
                return vector
    if isinstance(payload, list):
        for value in payload:
            vector = _extract_vector(value)
            if vector:
                return vector
    return None


def _text2vec(args: argparse.Namespace) -> dict[str, Any]:
    latencies: list[float] = []
    dimensions: list[int] = []
    payload = json.dumps({"text": args.text}).encode("utf-8")
    for _iteration in range(args.iterations):
        request = urllib.request.Request(
            args.url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        started = time.perf_counter()
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            parsed = json.loads(response.read())
        latencies.append((time.perf_counter() - started) * 1000)
        vector = _extract_vector(parsed)
        if not vector:
            raise RuntimeError
        dimensions.append(len(vector))
    return {
        "request_count": args.iterations,
        "inference_latency": _latency_summary(latencies),
        "vector_dimensions": sorted(set(dimensions)),
        "all_vectors_nonempty": all(dimension > 0 for dimension in dimensions),
    }


def _load_reranker_cases(path: str) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError
    return cases


def _candidate_key(candidate: dict[str, Any]) -> str:
    return f"{candidate.get('top_item_id')}:{candidate.get('bottom_item_id')}"


def _reranker(args: argparse.Namespace) -> dict[str, Any]:
    cases = _load_reranker_cases(args.cases)
    if args.dry_run:
        return {
            "dry_run": True,
            "case_count": len(cases),
            "all_expected_keys_present": all(
                case.get("expected_top")
                in {_candidate_key(candidate) for candidate in case["candidates"]}
                for case in cases
            ),
        }

    from attreq_api.config.settings import settings
    from attreq_api.services.recommendation.reranker import rerank

    settings.reranker_enabled = True
    settings.reranker_both_order = args.both_order
    latencies: list[float] = []
    successes = 0
    changed = 0
    expected_matches = 0
    top_keys: dict[str, str] = {}
    provider_error_counts = {
        "rate_limit": 0,
        "transient_5xx": 0,
        "timeout": 0,
        "other": 0,
    }

    class ProviderErrorCounter(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            if record.levelno < logging.WARNING:
                return
            message = record.getMessage().lower()
            if "429" in message or "rate limit" in message:
                provider_error_counts["rate_limit"] += 1
            elif any(code in message for code in ("502", "503", "504")):
                provider_error_counts["transient_5xx"] += 1
            elif "timeout" in message or "timed out" in message:
                provider_error_counts["timeout"] += 1
            elif "reranker" in message or "groq" in message:
                provider_error_counts["other"] += 1

    counter = ProviderErrorCounter()
    root_logger = logging.getLogger("attreq_api")
    root_logger.addHandler(counter)

    async def run_all() -> None:
        nonlocal successes, changed, expected_matches
        for _iteration in range(args.iterations):
            for case in cases:
                candidates = case["candidates"]
                started = time.perf_counter()
                reordered, rationales = await rerank(candidates, case["context"])
                latencies.append((time.perf_counter() - started) * 1000)
                original_top = _candidate_key(candidates[0])
                returned_top = _candidate_key(reordered[0])
                top_keys[str(case["name"])] = returned_top
                if rationales is not None:
                    successes += 1
                if returned_top != original_top:
                    changed += 1
                if returned_top == case.get("expected_top"):
                    expected_matches += 1

    try:
        asyncio.run(run_all())
    finally:
        root_logger.removeHandler(counter)
    request_count = len(cases) * args.iterations
    return {
        "case_count": len(cases),
        "iteration_count": args.iterations,
        "both_order": args.both_order,
        "latency": _latency_summary(latencies),
        "validated_response_rate": round(successes / request_count, 4),
        "display_order_change_rate": round(changed / request_count, 4),
        "expected_top_match_rate": round(expected_matches / request_count, 4),
        "last_top_key_by_case": top_keys,
        "provider_error_counts": provider_error_counts,
        "raw_rationales_recorded": False,
    }


def _baseline(args: argparse.Namespace) -> dict[str, Any]:
    # Hold briefly so container/API samplers have multiple observations.
    time.sleep(args.duration)
    return {"sample_duration_seconds": args.duration}


def _service_startup(args: argparse.Namespace) -> dict[str, Any]:
    compose_path = str(Path(args.compose_file).resolve())
    command = ["docker", "compose", "-f", compose_path, "--profile", args.profile]
    if args.recreate:
        subprocess.run(
            [*command, "rm", "--stop", "--force", args.service],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )

    started = time.perf_counter()
    subprocess.run(
        [*command, "up", "--detach", "--no-deps", args.service],
        check=True,
        capture_output=True,
        text=True,
        timeout=args.timeout,
    )
    attempts = 0
    status: int | None = None
    deadline = time.monotonic() + args.timeout
    body = args.ready_json.encode("utf-8") if args.ready_json else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    while time.monotonic() < deadline:
        attempts += 1
        try:
            request = urllib.request.Request(
                args.ready_url,
                data=body,
                headers=headers,
                method=args.ready_method,
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                status = response.status
                response.read(1)
            if 200 <= status < 300:
                break
        except urllib.error.HTTPError as error:
            status = error.code
        except (OSError, urllib.error.URLError):
            status = None
        time.sleep(args.poll_interval)
    else:
        raise TimeoutError

    return {
        "service": args.service,
        "profile": args.profile,
        "recreated": args.recreate,
        "ready_http_status": status,
        "ready_attempts": attempts,
        "startup_to_ready_ms": round((time.perf_counter() - started) * 1000, 3),
    }


def _docker_workload(args: argparse.Namespace) -> dict[str, Any]:
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise ValueError
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=args.timeout,
    )
    # ATTREQ's inner harness is the expected command. Never echo the command
    # itself or stderr: either could contain an env-file path or provider data.
    inner = json.loads(completed.stdout)
    if not isinstance(inner, dict) or inner.get("schema_version") != SCHEMA_VERSION:
        raise ValueError
    return {
        "inner_component": inner.get("component"),
        "inner_status": inner.get("status"),
        "inner_elapsed_ms": inner.get("elapsed_ms"),
        "inner_measurements": inner.get("measurements"),
    }


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output", help="Write the JSON result to this path as well as stdout")
    parser.add_argument(
        "--docker-container",
        action="append",
        default=[],
        help="Docker container name/id to sample; repeat for multiple containers",
    )
    parser.add_argument(
        "--probe-spec",
        help="Mode-0600 JSON file containing optional health/recommendation probes",
    )
    parser.add_argument("--sample-interval", type=float, default=0.5)


def _default_compose_file() -> Path:
    """Resolve the repository Compose file without assuming script depth.

    The harness is also copied into a shallow container path for inner
    FashionCLIP runs, where ``parents[3]`` does not exist. Component commands
    do not use this default, but argparse constructs every subparser eagerly.
    """
    script = Path(__file__).resolve()
    for parent in script.parents:
        candidate = parent / "infra/docker/compose.pi-benchmark.yml"
        if candidate.is_file():
            return candidate
    return Path("infra/docker/compose.pi-benchmark.yml")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="component", required=True)

    baseline = subparsers.add_parser("baseline", help="Record idle host/container/API metrics")
    _add_common(baseline)
    baseline.add_argument("--duration", type=float, default=10)
    baseline.set_defaults(handler=_baseline)

    startup = subparsers.add_parser(
        "service-startup", help="Start one disposable benchmark service and measure readiness"
    )
    _add_common(startup)
    default_compose = _default_compose_file()
    startup.add_argument("--compose-file", default=str(default_compose))
    startup.add_argument("--profile", required=True)
    startup.add_argument("--service", required=True)
    startup.add_argument("--ready-url", required=True)
    startup.add_argument("--ready-method", choices=("GET", "POST"), default="GET")
    startup.add_argument("--ready-json")
    startup.add_argument("--timeout", type=float, default=600)
    startup.add_argument("--poll-interval", type=float, default=1)
    startup.add_argument(
        "--recreate",
        action="store_true",
        help="Remove only the named BR-04 service before measuring cold startup",
    )
    startup.set_defaults(handler=_service_startup)

    docker_workload = subparsers.add_parser(
        "docker-workload",
        help="Sample host/container/API metrics around an inner JSON benchmark command",
    )
    _add_common(docker_workload)
    docker_workload.add_argument("--timeout", type=float, default=1800)
    docker_workload.add_argument("command", nargs=argparse.REMAINDER)
    docker_workload.set_defaults(handler=_docker_workload)

    fashionclip = subparsers.add_parser("fashionclip", help="Benchmark ATTREQ FashionCLIP")
    _add_common(fashionclip)
    fashionclip.add_argument("--image", action="append", required=True)
    fashionclip.add_argument("--iterations", type=int, default=10)
    fashionclip.set_defaults(handler=_fashionclip)

    weaviate_parser = subparsers.add_parser("weaviate", help="Benchmark manual vector storage")
    _add_common(weaviate_parser)
    weaviate_parser.add_argument("--host", default="127.0.0.1")
    weaviate_parser.add_argument("--http-port", type=int, default=18080)
    weaviate_parser.add_argument("--grpc-port", type=int, default=15051)
    weaviate_parser.add_argument("--objects", type=int, default=100)
    weaviate_parser.add_argument("--queries", type=int, default=30)
    weaviate_parser.add_argument("--dimension", type=int, default=512)
    weaviate_parser.add_argument("--seed", type=int, default=20260812)
    weaviate_parser.set_defaults(handler=_weaviate)

    text2vec = subparsers.add_parser("text2vec", help="Benchmark transformer inference HTTP")
    _add_common(text2vec)
    text2vec.add_argument("--url", default="http://127.0.0.1:19090/vectors")
    text2vec.add_argument("--text", default="navy cotton shirt for a casual warm day")
    text2vec.add_argument("--iterations", type=int, default=30)
    text2vec.add_argument("--timeout", type=float, default=60)
    text2vec.set_defaults(handler=_text2vec)

    reranker = subparsers.add_parser("reranker", help="Benchmark the real ATTREQ LLM reranker")
    _add_common(reranker)
    default_cases = Path(__file__).with_name("br04_reranker_cases.json")
    reranker.add_argument("--cases", default=str(default_cases))
    reranker.add_argument("--iterations", type=int, default=3)
    reranker.add_argument("--both-order", action="store_true")
    reranker.add_argument("--dry-run", action="store_true")
    reranker.set_defaults(handler=_reranker)
    return parser


def main() -> int:
    args = _parser().parse_args()
    result = _run_measured(args, lambda: args.handler(args))
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(output.suffix + ".tmp")
        temporary.write_text(rendered + "\n", encoding="utf-8")
        temporary.replace(output)
    print(rendered)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
