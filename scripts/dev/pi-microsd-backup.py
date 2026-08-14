#!/usr/bin/env python3
"""PostgreSQL backup lifecycle for the ATTREQ Raspberry Pi microSD beta.

The tool streams pg_dump directly into a gzip staging file, uploads it to a
dedicated prefix in the existing private R2 bucket, verifies the uploaded bytes,
and applies a conservative 7-daily/4-weekly retention policy. It never reads or
prints secret values and never restores over the live database.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BASE_COMPOSE = REPOSITORY_ROOT / "infra/docker/compose.pi-beta.yml"
MICROSD_COMPOSE = REPOSITORY_ROOT / "infra/docker/compose.pi-microsd.yml"
R2_PREFIX = "attreq-db-backups/postgres/"
CONTAINER_BACKUP_DIR = Path("/var/lib/attreq-backups")
MIN_BACKUP_FREE_BYTES = 2 * 1024**3
DATABASE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")
KEY_RE = re.compile(
    r"^attreq-db-backups/postgres/"
    r"(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/"
    r"attreq-postgres-(?P<stamp>\d{8}T\d{6}Z)-"
    r"(?P<nonce>[0-9a-f]{12})\.sql\.gz$"
)


UPLOAD_PROGRAM = r"""
import hashlib, json, os
import boto3

required = ["S3_ENDPOINT_URL", "S3_BUCKET", "S3_ACCESS_KEY_ID", "S3_SECRET_ACCESS_KEY"]
missing = [name for name in required if not os.environ.get(name)]
if missing:
    raise SystemExit("missing required R2 configuration: " + ", ".join(missing))
path = os.path.realpath(os.environ["ATTREQ_BACKUP_FILE"])
root = "/var/lib/attreq-backups/"
if not path.startswith(root):
    raise SystemExit("backup file is outside the read-only staging mount")
key = os.environ["ATTREQ_BACKUP_KEY"]
if not key.startswith("attreq-db-backups/postgres/"):
    raise SystemExit("refusing upload outside the dedicated database-backup prefix")
expected = os.environ["ATTREQ_BACKUP_SHA256"]
client = boto3.client(
    "s3",
    endpoint_url=os.environ["S3_ENDPOINT_URL"],
    aws_access_key_id=os.environ["S3_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["S3_SECRET_ACCESS_KEY"],
    region_name="auto",
)
with open(path, "rb") as body:
    client.put_object(
        Bucket=os.environ["S3_BUCKET"],
        Key=key,
        Body=body,
        ContentType="application/gzip",
        Metadata={
            "sha256": expected,
            "attreq-backup-kind": "postgres",
            "attreq-backup-format": "plain-sql-gzip",
            "created-utc": os.environ["ATTREQ_BACKUP_CREATED_UTC"],
        },
    )
response = client.get_object(Bucket=os.environ["S3_BUCKET"], Key=key)
digest = hashlib.sha256()
size = 0
for chunk in iter(lambda: response["Body"].read(1024 * 1024), b""):
    digest.update(chunk)
    size += len(chunk)
response["Body"].close()
actual = digest.hexdigest()
if actual != expected:
    raise SystemExit("R2 post-upload SHA-256 verification failed")
head = client.head_object(Bucket=os.environ["S3_BUCKET"], Key=key)
if head.get("Metadata", {}).get("sha256") != expected or head["ContentLength"] != size:
    raise SystemExit("R2 post-upload metadata verification failed")
print(json.dumps({"key": key, "sha256": actual, "size": size}))
"""

LIST_PROGRAM = r"""
import json, os
import boto3

required = ["S3_ENDPOINT_URL", "S3_BUCKET", "S3_ACCESS_KEY_ID", "S3_SECRET_ACCESS_KEY"]
missing = [name for name in required if not os.environ.get(name)]
if missing:
    raise SystemExit("missing required R2 configuration: " + ", ".join(missing))
client = boto3.client(
    "s3",
    endpoint_url=os.environ["S3_ENDPOINT_URL"],
    aws_access_key_id=os.environ["S3_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["S3_SECRET_ACCESS_KEY"],
    region_name="auto",
)
objects = []
pages = client.get_paginator("list_objects_v2").paginate(
    Bucket=os.environ["S3_BUCKET"], Prefix="attreq-db-backups/postgres/"
)
for page in pages:
    for item in page.get("Contents", []):
        head = client.head_object(Bucket=os.environ["S3_BUCKET"], Key=item["Key"])
        objects.append({
            "key": item["Key"],
            "size": item["Size"],
            "last_modified": item["LastModified"].isoformat(),
            "metadata": head.get("Metadata", {}),
        })
print(json.dumps(objects))
"""

DELETE_PROGRAM = r"""
import json, os
import boto3

keys = json.loads(os.environ["ATTREQ_DELETE_KEYS"])
if not isinstance(keys, list) or not keys:
    raise SystemExit("no backup keys supplied")
if any(not isinstance(key, str) or not key.startswith("attreq-db-backups/postgres/") for key in keys):
    raise SystemExit("refusing deletion outside the dedicated database-backup prefix")
client = boto3.client(
    "s3",
    endpoint_url=os.environ["S3_ENDPOINT_URL"],
    aws_access_key_id=os.environ["S3_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["S3_SECRET_ACCESS_KEY"],
    region_name="auto",
)
response = client.delete_objects(
    Bucket=os.environ["S3_BUCKET"],
    Delete={"Objects": [{"Key": key} for key in keys], "Quiet": False},
)
errors = response.get("Errors", [])
if errors:
    raise SystemExit("R2 reported one or more retention deletion failures")
print(json.dumps({"deleted": len(response.get("Deleted", []))}))
"""

HEAD_PROGRAM = r"""
import json, os
import boto3

key = os.environ["ATTREQ_BACKUP_KEY"]
if not key.startswith("attreq-db-backups/postgres/"):
    raise SystemExit("refusing download outside the dedicated database-backup prefix")
client = boto3.client(
    "s3",
    endpoint_url=os.environ["S3_ENDPOINT_URL"],
    aws_access_key_id=os.environ["S3_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["S3_SECRET_ACCESS_KEY"],
    region_name="auto",
)
head = client.head_object(Bucket=os.environ["S3_BUCKET"], Key=key)
print(json.dumps({"size": head["ContentLength"], "metadata": head.get("Metadata", {})}))
"""

DOWNLOAD_PROGRAM = r"""
import os, sys
import boto3

key = os.environ["ATTREQ_BACKUP_KEY"]
if not key.startswith("attreq-db-backups/postgres/"):
    raise SystemExit("refusing download outside the dedicated database-backup prefix")
client = boto3.client(
    "s3",
    endpoint_url=os.environ["S3_ENDPOINT_URL"],
    aws_access_key_id=os.environ["S3_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["S3_SECRET_ACCESS_KEY"],
    region_name="auto",
)
response = client.get_object(Bucket=os.environ["S3_BUCKET"], Key=key)
for chunk in iter(lambda: response["Body"].read(1024 * 1024), b""):
    sys.stdout.buffer.write(chunk)
response["Body"].close()
"""


class BackupError(RuntimeError):
    """An operator-safe backup lifecycle failure."""


@dataclass(frozen=True)
class BackupObject:
    key: str
    created: dt.datetime


def operator_environment() -> tuple[Path, Path]:
    data_dir = Path(os.environ.get("ATTREQ_DATA_DIR", "/var/lib/attreq"))
    env_file = Path(os.environ.get("ATTREQ_ENV_FILE", "/etc/attreq/pi-beta.env"))
    if not data_dir.is_absolute() or not env_file.is_absolute():
        raise BackupError("ATTREQ_DATA_DIR and ATTREQ_ENV_FILE must be absolute paths")
    return data_dir, env_file


def require_environment() -> tuple[Path, Path]:
    data_dir, env_file = operator_environment()
    if not env_file.is_file() or env_file.is_symlink():
        raise BackupError(f"missing regular secret environment file: {env_file}")
    mode = stat.S_IMODE(env_file.stat().st_mode)
    if mode != 0o600:
        raise BackupError(f"secret environment file must have mode 0600 (current: {mode:04o})")
    if not data_dir.is_dir():
        raise BackupError(f"missing ATTREQ data directory: {data_dir}")
    return data_dir, env_file


def compose_command(*arguments: str) -> list[str]:
    data_dir, env_file = operator_environment()
    return [
        "docker",
        "compose",
        "--env-file",
        str(env_file),
        "-f",
        str(BASE_COMPOSE),
        "-f",
        str(MICROSD_COMPOSE),
        *arguments,
    ]


def compose_environment() -> dict[str, str]:
    data_dir, env_file = operator_environment()
    return {
        **os.environ,
        "ATTREQ_DATA_DIR": str(data_dir),
        "ATTREQ_ENV_FILE": str(env_file),
    }


def run_compose(
    *arguments: str,
    capture_output: bool = False,
    text: bool = True,
) -> subprocess.CompletedProcess[Any]:
    try:
        return subprocess.run(
            compose_command(*arguments),
            env=compose_environment(),
            check=True,
            capture_output=capture_output,
            text=text,
        )
    except FileNotFoundError as error:
        raise BackupError("Docker Engine and the Docker Compose plugin are required") from error
    except subprocess.CalledProcessError as error:
        raise BackupError(f"Docker Compose command failed with exit code {error.returncode}") from error


def validate_compose() -> None:
    run_compose("config", "--quiet", capture_output=True)


def now_and_key() -> tuple[dt.datetime, str]:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    key = (
        f"{R2_PREFIX}{now:%Y/%m/%d}/"
        f"attreq-postgres-{stamp}-{uuid.uuid4().hex[:12]}.sql.gz"
    )
    return now, key


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_gzip(path: Path) -> None:
    try:
        with gzip.open(path, "rb") as stream:
            for _ in iter(lambda: stream.read(1024 * 1024), b""):
                pass
    except (OSError, EOFError) as error:
        raise BackupError(f"gzip integrity verification failed for {path}") from error


def ensure_backup_space(directory: Path) -> None:
    free = shutil.disk_usage(directory).free
    if free < MIN_BACKUP_FREE_BYTES:
        raise BackupError("fewer than 2 GiB are available for backup staging")


def create_dump(staging: Path) -> None:
    partial = staging.with_suffix(staging.suffix + ".partial")
    if partial.exists() or staging.exists():
        raise BackupError(f"refusing to overwrite existing staging file: {staging}")
    command = compose_command(
        "exec",
        "-T",
        "postgres",
        "sh",
        "-ec",
        'exec pg_dump --no-owner --no-privileges -U "$POSTGRES_USER" "$POSTGRES_DB"',
    )
    process: subprocess.Popen[bytes] | None = None
    try:
        process = subprocess.Popen(
            command,
            env=compose_environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        if process.stdout is None:
            raise BackupError("failed to open pg_dump output stream")
        with partial.open("xb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=0) as zipped:
                shutil.copyfileobj(process.stdout, zipped, length=1024 * 1024)
            raw.flush()
            os.fsync(raw.fileno())
        return_code = process.wait()
        if return_code != 0:
            raise BackupError(f"pg_dump failed with exit code {return_code}")
        partial.replace(staging)
        verify_gzip(staging)
    except FileNotFoundError as error:
        raise BackupError("Docker Engine and the Docker Compose plugin are required") from error
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
        partial.unlink(missing_ok=True)


def backend_json(program: str, extra_environment: dict[str, str] | None = None) -> Any:
    arguments = ["exec", "-T"]
    for name, value in sorted((extra_environment or {}).items()):
        arguments.extend(["-e", f"{name}={value}"])
    arguments.extend(["backend", "python", "-c", program])
    result = run_compose(*arguments, capture_output=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise BackupError("R2 helper returned malformed output") from error


def upload(staging: Path, key: str, created: dt.datetime, digest: str) -> dict[str, Any]:
    container_path = CONTAINER_BACKUP_DIR / staging.name
    result = backend_json(
        UPLOAD_PROGRAM,
        {
            "ATTREQ_BACKUP_FILE": str(container_path),
            "ATTREQ_BACKUP_KEY": key,
            "ATTREQ_BACKUP_SHA256": digest,
            "ATTREQ_BACKUP_CREATED_UTC": created.isoformat().replace("+00:00", "Z"),
        },
    )
    if result.get("key") != key or result.get("sha256") != digest:
        raise BackupError("R2 upload verification returned unexpected data")
    return result


def parse_recognized_objects(raw_objects: Sequence[dict[str, Any]]) -> tuple[list[BackupObject], list[str]]:
    recognized: list[BackupObject] = []
    skipped: list[str] = []
    for item in raw_objects:
        key = item.get("key")
        match = KEY_RE.fullmatch(key) if isinstance(key, str) else None
        metadata = item.get("metadata")
        if (
            match is None
            or not isinstance(metadata, dict)
            or metadata.get("attreq-backup-kind") != "postgres"
            or re.fullmatch(r"[0-9a-f]{64}", str(metadata.get("sha256", ""))) is None
        ):
            if isinstance(key, str):
                skipped.append(key)
            continue
        created = dt.datetime.strptime(match.group("stamp"), "%Y%m%dT%H%M%SZ").replace(
            tzinfo=dt.timezone.utc
        )
        if created.strftime("%Y/%m/%d") != (
            f"{match.group('year')}/{match.group('month')}/{match.group('day')}"
        ):
            skipped.append(key)
            continue
        recognized.append(BackupObject(key=key, created=created))
    return sorted(recognized, key=lambda item: item.created, reverse=True), skipped


def retention_plan(objects: Sequence[BackupObject]) -> tuple[set[str], set[str]]:
    """Keep newest snapshot for seven UTC days and four ISO weeks."""
    daily: dict[dt.date, BackupObject] = {}
    weekly: dict[tuple[int, int], BackupObject] = {}
    for item in sorted(objects, key=lambda candidate: candidate.created, reverse=True):
        if len(daily) < 7:
            daily.setdefault(item.created.date(), item)
        iso = item.created.isocalendar()
        if len(weekly) < 4:
            weekly.setdefault((iso.year, iso.week), item)
    keep = {item.key for item in daily.values()} | {item.key for item in weekly.values()}
    delete = {item.key for item in objects} - keep
    return keep, delete


def prune(dry_run: bool) -> tuple[int, int]:
    raw = backend_json(LIST_PROGRAM)
    if not isinstance(raw, list):
        raise BackupError("R2 listing returned unexpected data")
    objects, skipped = parse_recognized_objects(raw)
    keep, delete = retention_plan(objects)
    for key in skipped:
        print(f"retention skipped unrecognized object: {key}")
    if delete:
        if dry_run:
            for key in sorted(delete):
                print(f"would delete: {key}")
        else:
            backend_json(DELETE_PROGRAM, {"ATTREQ_DELETE_KEYS": json.dumps(sorted(delete))})
            for key in sorted(delete):
                print(f"deleted expired backup: {key}")
    print(f"retention: {len(keep)} kept, {len(delete)} {'planned for deletion' if dry_run else 'deleted'}")
    return len(keep), len(delete)


def command_backup(dry_run: bool, keep_local: bool, no_prune: bool) -> None:
    data_dir, _ = require_environment()
    validate_compose()
    backup_dir = data_dir / "backups"
    if not backup_dir.is_dir() or backup_dir.is_symlink():
        raise BackupError(f"missing regular backup staging directory: {backup_dir}")
    created, key = now_and_key()
    staging = backup_dir / Path(key).name
    if dry_run:
        print(f"dry run: would stream pg_dump to {staging}.partial")
        print(f"dry run: would verify and upload to R2 key {key}")
        print("dry run: would apply retention only below attreq-db-backups/postgres/")
        return
    ensure_backup_space(backup_dir)
    create_dump(staging)
    digest = sha256_file(staging)
    result = upload(staging, key, created, digest)
    print(f"verified R2 backup: {key} ({result['size']} bytes, sha256 {digest})")
    try:
        if not no_prune:
            prune(dry_run=False)
    except Exception:
        print(f"retention failed; preserving verified local staging file: {staging}", file=sys.stderr)
        raise
    if keep_local:
        print(f"preserved local staging file: {staging}")
    else:
        staging.unlink()
        print("removed local staging file after verified R2 upload")


def validate_download_key(key: str) -> None:
    if KEY_RE.fullmatch(key) is None:
        raise BackupError("download key is not a recognized ATTREQ PostgreSQL backup key")


def download(key: str, output: Path, dry_run: bool) -> None:
    validate_download_key(key)
    require_environment()
    validate_compose()
    if output.exists() or output.with_suffix(output.suffix + ".partial").exists():
        raise BackupError(f"refusing to overwrite download path: {output}")
    if dry_run:
        print(f"dry run: would download {key} to {output}")
        return
    output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    head = backend_json(HEAD_PROGRAM, {"ATTREQ_BACKUP_KEY": key})
    metadata = head.get("metadata", {})
    expected = metadata.get("sha256")
    if metadata.get("attreq-backup-kind") != "postgres" or not isinstance(expected, str):
        raise BackupError("R2 object does not carry ATTREQ PostgreSQL integrity metadata")
    partial = output.with_suffix(output.suffix + ".partial")
    arguments = [
        "exec",
        "-T",
        "-e",
        f"ATTREQ_BACKUP_KEY={key}",
        "backend",
        "python",
        "-c",
        DOWNLOAD_PROGRAM,
    ]
    process: subprocess.Popen[bytes] | None = None
    digest = hashlib.sha256()
    size = 0
    try:
        process = subprocess.Popen(
            compose_command(*arguments),
            env=compose_environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        if process.stdout is None:
            raise BackupError("failed to open R2 download stream")
        with partial.open("xb") as target:
            for chunk in iter(lambda: process.stdout.read(1024 * 1024), b""):
                target.write(chunk)
                digest.update(chunk)
                size += len(chunk)
            target.flush()
            os.fsync(target.fileno())
        return_code = process.wait()
        if return_code != 0:
            raise BackupError(f"R2 download failed with exit code {return_code}")
        if digest.hexdigest() != expected or size != head.get("size"):
            raise BackupError("downloaded R2 backup failed SHA-256 or size verification")
        verify_gzip(partial)
        partial.replace(output)
        print(f"verified backup downloaded to {output} (sha256 {expected})")
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
        partial.unlink(missing_ok=True)


def restore_isolated(dump: Path, database: str, confirmed: bool) -> None:
    require_environment()
    validate_compose()
    if not confirmed:
        raise BackupError("isolated restore requires --confirm-isolated-restore")
    if DATABASE_RE.fullmatch(database) is None:
        raise BackupError("restore database name is invalid")
    if not dump.is_file() or dump.is_symlink() or dump.suffixes[-2:] != [".sql", ".gz"]:
        raise BackupError("restore source must be a regular .sql.gz file")
    verify_gzip(dump)
    create = run_compose(
        "exec",
        "-T",
        "-e",
        f"ATTREQ_RESTORE_DATABASE={database}",
        "postgres",
        "sh",
        "-ec",
        'target="$ATTREQ_RESTORE_DATABASE"; '
        'test "$target" != "$POSTGRES_DB" || exit 41; '
        # createdb fails closed when the target already exists; this tool never
        # drops, truncates, or reuses an existing database.
        'createdb -U "$POSTGRES_USER" "$target"',
        capture_output=True,
    )
    if create.returncode != 0:  # pragma: no cover - run_compose raises first
        raise BackupError("failed to create isolated restore database")
    command = compose_command(
        "exec",
        "-T",
        "-e",
        f"ATTREQ_RESTORE_DATABASE={database}",
        "postgres",
        "sh",
        "-ec",
        'test "$ATTREQ_RESTORE_DATABASE" != "$POSTGRES_DB"; '
        'exec psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$ATTREQ_RESTORE_DATABASE"',
    )
    process = subprocess.Popen(command, env=compose_environment(), stdin=subprocess.PIPE)
    try:
        if process.stdin is None:
            raise BackupError("failed to open isolated restore input stream")
        with gzip.open(dump, "rb") as source:
            shutil.copyfileobj(source, process.stdin, length=1024 * 1024)
        process.stdin.close()
        return_code = process.wait()
        if return_code != 0:
            raise BackupError(
                f"restore failed with exit code {return_code}; the isolated database was not removed"
            )
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
    print(f"isolated restore completed into {database}; the live database was not modified")


def self_test() -> None:
    base = dt.datetime(2026, 8, 14, 6, tzinfo=dt.timezone.utc)
    objects: list[BackupObject] = []
    for index in range(45):
        created = base - dt.timedelta(days=index // 3, hours=index % 3)
        objects.append(BackupObject(key=f"key-{index}", created=created))
    keep, delete = retention_plan(objects)
    assert keep.isdisjoint(delete)
    assert keep | delete == {item.key for item in objects}
    assert len({next(item.created.date() for item in objects if item.key == key) for key in keep}) >= 7
    assert len(keep) <= 11
    created, key = now_and_key()
    assert KEY_RE.fullmatch(key)
    assert created.tzinfo == dt.timezone.utc
    print("self-test passed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)

    backup = subcommands.add_parser("backup", help="create, upload, verify, and retain backups")
    backup.add_argument("--dry-run", action="store_true")
    backup.add_argument("--keep-local", action="store_true")
    backup.add_argument("--no-prune", action="store_true")

    prune_command = subcommands.add_parser("prune", help="apply safe R2 retention")
    prune_command.add_argument("--dry-run", action="store_true")

    download_command = subcommands.add_parser("download", help="download and verify one R2 backup")
    download_command.add_argument("key")
    download_command.add_argument("--output", type=Path, required=True)
    download_command.add_argument("--dry-run", action="store_true")

    restore = subcommands.add_parser(
        "restore-isolated", help="restore a local dump into a new non-live database"
    )
    restore.add_argument("dump", type=Path)
    restore.add_argument("--database", required=True)
    restore.add_argument("--confirm-isolated-restore", action="store_true")

    subcommands.add_parser("self-test", help="run offline naming and retention checks")
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    try:
        if arguments.command == "backup":
            command_backup(arguments.dry_run, arguments.keep_local, arguments.no_prune)
        elif arguments.command == "prune":
            require_environment()
            validate_compose()
            prune(arguments.dry_run)
        elif arguments.command == "download":
            download(arguments.key, arguments.output, arguments.dry_run)
        elif arguments.command == "restore-isolated":
            restore_isolated(
                arguments.dump, arguments.database, arguments.confirm_isolated_restore
            )
        else:
            self_test()
    except BackupError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
