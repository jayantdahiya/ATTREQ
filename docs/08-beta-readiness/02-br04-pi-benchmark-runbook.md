# BR-04 Raspberry Pi Optional-Component Benchmark

> **Status:** Prepared, not executed on the Pi
> **Last verified:** 2026-08-12
> **Purpose:** Measure FashionCLIP, Weaviate, `text2vec-transformers`, and the Groq reranker independently before choosing the beta topology.

## Safety and Known Baseline

This runbook is intentionally separate from production deployment. The Compose file binds temporary service ports to `127.0.0.1`, uses the `attreq-br04` project, and must never receive production data. Run only one optional component at a time.

The Pi was inspected read-only on 2026-08-12: Raspberry Pi 5, ARM64 Cortex-A76, four cores, 7.7 GiB RAM, no swap, and `/mnt/storage` has approximately 217 GiB available. Docker is not installed, so no live results exist yet.

Registry manifests were checked on the same date:

| Component | Candidate | Native ARM64 finding |
|---|---|---|
| Weaviate | `cr.weaviate.io/semitechnologies/weaviate:1.27.0` | `linux/arm64` manifest exists |
| Transformer | `cr.weaviate.io/semitechnologies/transformers-inference:sentence-transformers-all-MiniLM-L6-v2` | `linux/arm64` manifest exists |
| API/FashionCLIP | `python:3.11-slim` plus repository dependencies | Base image supports ARM64; requirements now select `torch==2.2.2` on Linux AArch64 because the `2.2.2+cpu` filename is x86-only |
| Reranker | Remote Groq call from API | No local inference image; assess latency, failures, limits, and ranking value |

The current product paths are distinct:

- FashionCLIP: `apps/api/src/attreq_api/services/ai/fashion_embeddings.py`, gated by `EMBEDDINGS_ENABLED` at callers.
- Manual FashionCLIP vectors: Weaviate `ClothingItemVector`, which does not need a vectorizer.
- Legacy semantic text search: Weaviate `ClothingItem`, which does need the transformer sidecar.
- Groq reranker: `apps/api/src/attreq_api/services/recommendation/reranker.py`, gated by `RERANKER_ENABLED`.

Do not infer one component's result from another component's result.

## Files and Result Handling

- Harness: `apps/api/scripts/benchmark_pi_components.py`
- Synthetic reranker cases: `apps/api/scripts/br04_reranker_cases.json`
- Disposable services: `infra/docker/compose.pi-benchmark.yml`
- Raw output location on Pi: `/mnt/storage/attreq/benchmarks/results/<UTC timestamp>/`

Raw JSON may contain hostnames and timings, so keep it out of Git. The harness deliberately omits environment variables, headers, response bodies, image paths, and LLM rationales. If API probes require a bearer token, put them in a mode-`0600` file outside the checkout. Never pass a token on the command line.

Example probe file:

```json
{
  "probes": [
    {"name": "health", "url": "http://127.0.0.1:8000/health"},
    {
      "name": "recommendation",
      "url": "http://127.0.0.1:8000/api/v1/recommendations/daily?force_refresh=true",
      "headers": {"Authorization": "Bearer REPLACE_LOCALLY"},
      "timeout_seconds": 30
    }
  ]
}
```

Immediately run `chmod 600 /path/to/probes.json`. Delete or revoke its token after testing.

## One-Time Prerequisites

These actions require explicit authorization because they change the Pi:

1. Install current Docker Engine and Compose plugin using the official Ubuntu ARM64 instructions.
2. Clone a reviewed ATTREQ commit on the Pi.
3. Create `/mnt/storage/attreq/benchmarks/{results,weaviate,huggingface}` owned by the deployment user.
4. Confirm `docker version`, `docker compose version`, `uname -m` = `aarch64`, and at least 6 GiB memory available.
5. Do not expose benchmark ports in the router, firewall, or Cloudflare Tunnel.

From the repository root:

```bash
export ATTREQ_BENCHMARK_DATA_DIR=/mnt/storage/attreq/benchmarks
ATTREQ_BENCHMARK_RUN="$ATTREQ_BENCHMARK_DATA_DIR/results/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$ATTREQ_BENCHMARK_RUN"
chmod 700 "$ATTREQ_BENCHMARK_RUN"

docker buildx imagetools inspect cr.weaviate.io/semitechnologies/weaviate:1.27.0
docker buildx imagetools inspect \
  cr.weaviate.io/semitechnologies/transformers-inference:sentence-transformers-all-MiniLM-L6-v2
docker compose -f infra/docker/compose.pi-benchmark.yml config --profiles
```

If any selected manifest resolves to `linux/amd64`, stop. Do not use QEMU/emulation for a passing result.

## Protocol and Gates

Run each scenario twice after its first download: a cold service/model start and a warm repeat. Then reboot the Pi and repeat the proposed final configuration. Record ambient load and note any thermal throttling separately.

The Pi has no swap. Use these beta gates:

| Metric | Pass gate |
|---|---|
| Native architecture | Must run as `linux/arm64`, with no emulation |
| Total available memory under load | Never below 1.5 GiB |
| Optional-component aggregate peak memory | At most 4.0 GiB above the minimal API/PostgreSQL/Redis baseline |
| Sustained host CPU | Mean below 85%; brief peaks allowed |
| Temperature | Peak below 80°C and no throttling observed |
| Health probe | 100% HTTP 2xx; p95 below 500 ms while optional workload runs |
| Recommendation probe | No new 5xx; p95 no worse than baseline by over 1 second or 25%, whichever is larger |
| FashionCLIP | Valid 512-d vectors; warm p95 ≤ 5 s/image; five jobs finish without OOM/API instability |
| Weaviate manual vectors | 100 inserts and 30 queries succeed; query p95 ≤ 250 ms |
| Transformer | Non-empty vectors; warm p95 ≤ 2 s/request; no OOM/API instability |
| Reranker | ≥95% validated responses, zero unhandled errors, p95 ≤ 8 s, expected-top rate improves over the synthetic heuristic baseline |

A component also needs observable product value. A technical pass without ranking/search value stays disabled. A failed component remains feature-gated; do not delete its implementation.

## 1. Minimal Baseline

Run the minimal BR-05 API/PostgreSQL/Redis stack first, then record ten minutes of idle and representative upload/recommendation traffic. Substitute its real container names and optional mode-`0600` probe path:

```bash
cd apps/api
PYTHONPATH=src ../../.venv/bin/python scripts/benchmark_pi_components.py baseline \
  --duration 600 \
  --docker-container attreq_backend \
  --docker-container attreq_postgres \
  --docker-container attreq_redis \
  --probe-spec /secure/path/probes.json \
  --output "$ATTREQ_BENCHMARK_RUN/baseline.json"
cd ../..
```

## 2. FashionCLIP Only

Build the API image natively. This is the required dependency-resolution gate; failure means FashionCLIP fails BR-04 until the ARM64 dependency path is fixed.

```bash
ATTREQ_BENCHMARK_ENV_FILE=/dev/null docker compose \
  -f infra/docker/compose.pi-benchmark.yml --profile api build api-runner
ATTREQ_BENCHMARK_ENV_FILE=/dev/null docker compose \
  -f infra/docker/compose.pi-benchmark.yml --profile api up -d api-runner
```

Use three to ten non-sensitive, representative background-removed garment fixtures. The tracked research image can prove mechanics but is not sufficient for the final decision.

```bash
apps/api/scripts/benchmark_pi_components.py docker-workload \
  --docker-container attreq_br04_api \
  --probe-spec /secure/path/probes.json \
  --output "$ATTREQ_BENCHMARK_RUN/fashionclip-cold.json" -- \
  docker exec attreq_br04_api python scripts/benchmark_pi_components.py fashionclip \
    --image /bench-fixtures/wardrobe_image.jpg --iterations 10

apps/api/scripts/benchmark_pi_components.py docker-workload \
  --docker-container attreq_br04_api \
  --probe-spec /secure/path/probes.json \
  --output "$ATTREQ_BENCHMARK_RUN/fashionclip-warm.json" -- \
  docker exec attreq_br04_api python scripts/benchmark_pi_components.py fashionclip \
    --image /bench-fixtures/wardrobe_image.jpg --iterations 10
```

## 3. Weaviate Manual Vectors Only

This profile starts Weaviate without `text2vec-transformers` and measures the manual 512-d collection used by FashionCLIP.

```bash
PYTHONPATH=apps/api/src .venv/bin/python apps/api/scripts/benchmark_pi_components.py service-startup \
  --profile weaviate --service weaviate-manual --recreate \
  --ready-url http://127.0.0.1:18080/v1/.well-known/ready \
  --docker-container attreq_br04_weaviate \
  --output "$ATTREQ_BENCHMARK_RUN/weaviate-startup.json"

PYTHONPATH=apps/api/src .venv/bin/python apps/api/scripts/benchmark_pi_components.py weaviate \
  --host 127.0.0.1 --http-port 18080 --grpc-port 15051 \
  --objects 100 --queries 30 --dimension 512 \
  --docker-container attreq_br04_weaviate \
  --probe-spec /secure/path/probes.json \
  --output "$ATTREQ_BENCHMARK_RUN/weaviate.json"
```

The harness creates a uniquely named collection and deletes only that collection.

## 4. `text2vec-transformers` Only

Stop Weaviate before testing the transformer so its resource result remains independent.

```bash
docker compose -f infra/docker/compose.pi-benchmark.yml --profile weaviate stop weaviate-manual

PYTHONPATH=apps/api/src .venv/bin/python apps/api/scripts/benchmark_pi_components.py service-startup \
  --profile text2vec --service text2vec-transformers --recreate \
  --ready-url http://127.0.0.1:19090/vectors --ready-method POST \
  --ready-json '{"text":"warmup"}' \
  --docker-container attreq_br04_text2vec \
  --output "$ATTREQ_BENCHMARK_RUN/text2vec-startup.json"

PYTHONPATH=apps/api/src .venv/bin/python apps/api/scripts/benchmark_pi_components.py text2vec \
  --url http://127.0.0.1:19090/vectors --iterations 30 \
  --docker-container attreq_br04_text2vec \
  --probe-spec /secure/path/probes.json \
  --output "$ATTREQ_BENCHMARK_RUN/text2vec.json"
```

## 5. Groq Reranker Only

Stop all local optional services. Use the existing mode-`0600` backend environment outside Git; do not echo it or pass the key as an argument. The cases contain no user data. First verify mechanics without making a provider call:

```bash
docker compose -f infra/docker/compose.pi-benchmark.yml --profile text2vec stop text2vec-transformers

cd apps/api
PYTHONPATH=src ../../.venv/bin/python scripts/benchmark_pi_components.py reranker \
  --dry-run --output "$ATTREQ_BENCHMARK_RUN/reranker-dry-run.json"

set -a
. /secure/path/attreq-beta.env
set +a
PYTHONPATH=src ../../.venv/bin/python scripts/benchmark_pi_components.py reranker \
  --iterations 5 \
  --probe-spec /secure/path/probes.json \
  --output "$ATTREQ_BENCHMARK_RUN/reranker.json"
cd ../..
```

Run `--both-order` as a separate experiment because it doubles the maximum LLM calls. The JSON stores only aggregate provider-error categories and selected synthetic pair keys, never model rationales.

## Results and Decision Template

Copy this table into the BR-04 section of `00-immediate-beta-readiness.md` after reviewing raw JSON. Do not commit raw results, tokens, real user data, or precise private host details.

| Component | Native ARM64 | Cold start | Steady/peak RAM | CPU/temperature | Workload p50/p95 | API impact | Product value | Decision |
|---|---|---:|---:|---:|---:|---|---|---|
| FashionCLIP | TBD | TBD | TBD | TBD | image TBD/TBD | TBD | duplicate/style signal TBD | Enable/disable TBD |
| Weaviate manual vectors | TBD | TBD | TBD | TBD | insert TBD/TBD; query TBD/TBD | TBD | vector persistence/query TBD | Enable/disable TBD |
| `text2vec-transformers` | TBD | TBD | TBD | TBD | inference TBD/TBD | TBD | legacy text search TBD | Enable/disable TBD |
| Groq reranker | N/A remote | N/A | TBD Pi overhead | TBD | request TBD/TBD | TBD | valid %, expected-top %, qualitative review | Enable/disable TBD |

Record additionally:

- tested Git commit and image digests;
- cold/warm/reboot run timestamps;
- whether throttling, OOM, restart, provider 429/5xx, or malformed response occurred;
- baseline vs optional-component health/recommendation p95;
- exact feature flags selected for BR-05 and the reason for each.

## Cleanup

The commands below remove only the `attreq-br04` containers/network. They preserve Weaviate and Hugging Face benchmark caches for repeatability.

```bash
docker compose -f infra/docker/compose.pi-benchmark.yml --profile api --profile weaviate --profile text2vec down --remove-orphans
docker ps -a --filter name=attreq_br04
ss -ltn | rg ':(18080|15051|19090)\b' || true
```

After the decision is recorded, remove the temporary probe file and revoke its test token. Do not delete `/mnt/storage/attreq/benchmarks` until the summarized decision is committed and reviewed.

## Completion Checklist

- [ ] Docker installation/change authorization received.
- [ ] Native image and API-build gates pass on the Pi.
- [ ] Minimal baseline recorded.
- [ ] Cold, warm, concurrent, and API-impact measurements exist for each component.
- [ ] Proposed final configuration survives a Pi reboot.
- [ ] Each component has an explicit enable/disable decision with evidence.
- [ ] BR-05 Compose profiles/flags reflect those decisions.
- [ ] Sanitized summary is committed; raw data and secrets remain untracked.
