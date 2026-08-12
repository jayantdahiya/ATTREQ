#!/usr/bin/env bash
# Safe operator commands for infra/docker/compose.pi-beta.yml.
# This script never removes Docker volumes or bind-mounted application data.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/infra/docker/compose.pi-beta.yml"
DATA_DIR="${ATTREQ_DATA_DIR:-/mnt/storage/attreq}"
ENV_FILE="${ATTREQ_ENV_FILE:-$DATA_DIR/secrets/pi-beta.env}"

usage() {
  cat <<'EOF'
Usage: scripts/dev/pi-beta.sh <command> [arguments]

Commands:
  validate                 Validate the resolved Compose configuration.
  init-dirs                Create required SSD directories without deleting data.
  up                       Build/start the selected stack; migrations must succeed first.
  status                   Show service state and query the backend health endpoint.
  logs [service...]        Follow Compose logs (all services by default).
  backup                   Write a timestamped compressed PostgreSQL dump to backups/.
  restore <dump.sql.gz>    Restore one explicit dump; also requires ATTREQ_CONFIRM_RESTORE=RESTORE.
  rollback <image-tag>     Recreate the stack from an already-present backend image tag.
  down                     Stop containers while preserving all bind-mounted data.

The Pi secret env file is external to Git. Override its path with ATTREQ_ENV_FILE.
EOF
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

require_docker() {
  command -v docker >/dev/null 2>&1 || die "Docker Engine and Docker Compose plugin are required"
  docker compose version >/dev/null 2>&1 || die "Docker Compose plugin is required"
}

require_env_file() {
  [[ -f "$ENV_FILE" ]] || die "missing Pi secret env file: $ENV_FILE"
  [[ ! -L "$ENV_FILE" ]] || die "Pi secret env file must not be a symlink: $ENV_FILE"
  local mode
  mode="$(stat -c '%a' "$ENV_FILE" 2>/dev/null || stat -f '%Lp' "$ENV_FILE")"
  [[ "$mode" == "600" ]] || die "Pi secret env file must have mode 600 (current: $mode)"
}

compose() {
  ATTREQ_ENV_FILE="$ENV_FILE" ATTREQ_DATA_DIR="$DATA_DIR" \
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

ensure_new_service_dir() {
  local path="$1"
  if [[ -e "$path" ]]; then
    [[ -d "$path" ]] || die "expected directory, found non-directory: $path"
    return
  fi
  sudo install -d -m 0750 "$path"
}

initialize_service_dir() {
  local path="$1"
  local image="$2"
  local owner="$3"
  local mode="$4"
  if [[ -e "$path" ]]; then
    [[ -d "$path" ]] || die "expected directory, found non-directory: $path"
    printf 'preserving existing service directory: %s\n' "$path"
    return
  fi
  sudo install -d -m "$mode" "$path"
  # Resolve the named account from the exact image that owns this bind mount;
  # do not assume a host UID/GID. Docker executes this one-time setup as root.
  docker run --rm --user root -v "$path:/data" "$image" \
    sh -c "chown $owner /data && chmod $mode /data"
}

init_dirs() {
  [[ "$DATA_DIR" = /* ]] || die "ATTREQ_DATA_DIR must be an absolute path"
  sudo install -d -m 0750 "$DATA_DIR"
  for dir in backups uploads secrets weaviate transformer-cache; do
    ensure_new_service_dir "$DATA_DIR/$dir"
  done
  initialize_service_dir "$DATA_DIR/postgres" "postgres:15-alpine" "postgres:postgres" "0700"
  initialize_service_dir "$DATA_DIR/redis" "redis:7-alpine" "redis:redis" "0750"
  printf 'initialized non-destructively under %s\n' "$DATA_DIR"
}

validate() {
  require_docker
  require_env_file
  compose config --quiet
  printf 'Compose configuration is valid.\n'
}

up() {
  validate
  [[ -d "$DATA_DIR/postgres" && -d "$DATA_DIR/redis" && -d "$DATA_DIR/uploads" ]] || \
    die "run '$0 init-dirs' before first start"
  compose up -d --build
  compose ps
}

status() {
  require_docker
  require_env_file
  compose ps
  compose exec -T backend curl --fail --silent --show-error http://localhost:8000/health
  printf '\n'
}

logs() {
  require_docker
  require_env_file
  compose logs --follow --tail=200 "$@"
}

backup() {
  require_docker
  require_env_file
  [[ -d "$DATA_DIR/backups" ]] || die "backup directory is missing; run '$0 init-dirs'"
  umask 077
  local stamp output temporary
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  output="$DATA_DIR/backups/attreq-postgres-$stamp.sql.gz"
  temporary="$output.partial"
  trap 'rm -f "$temporary"' RETURN
  compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' | gzip -9 > "$temporary"
  mv "$temporary" "$output"
  trap - RETURN
  printf 'backup written: %s\n' "$output"
}

restore() {
  require_docker
  require_env_file
  local dump="${1:-}"
  local restore_database="${ATTREQ_RESTORE_DATABASE:-}"
  [[ -n "$dump" ]] || die "restore requires an explicit .sql.gz file path"
  [[ -f "$dump" ]] || die "restore file does not exist: $dump"
  [[ "$dump" == *.sql.gz ]] || die "restore file must end in .sql.gz"
  [[ "$restore_database" =~ ^[A-Za-z_][A-Za-z0-9_]{0,62}$ ]] || \
    die "set ATTREQ_RESTORE_DATABASE to a valid, isolated PostgreSQL database name"
  [[ "${ATTREQ_CONFIRM_RESTORE:-}" == "RESTORE" ]] || \
    die "restore creates an isolated database; rerun with ATTREQ_CONFIRM_RESTORE=RESTORE"
  gzip -t "$dump"
  compose up -d postgres
  local attempt ready=false
  for attempt in {1..30}; do
    if compose exec -T postgres sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' >/dev/null 2>&1; then
      ready=true
      break
    fi
    sleep 2
  done
  [[ "$ready" == true ]] || die "PostgreSQL did not become ready within 60 seconds"
  compose exec -T -e ATTREQ_RESTORE_DATABASE="$restore_database" postgres sh -c \
    'test "$ATTREQ_RESTORE_DATABASE" != "$POSTGRES_DB"' || \
    die "ATTREQ_RESTORE_DATABASE must differ from the live POSTGRES_DB"
  if compose exec -T -e ATTREQ_RESTORE_DATABASE="$restore_database" postgres sh -c \
    'psql -tAc "SELECT 1 FROM pg_database WHERE datname = '\''$ATTREQ_RESTORE_DATABASE'\''" -U "$POSTGRES_USER"' | grep -qx '1'; then
    die "restore target database already exists: $restore_database"
  fi
  compose exec -T -e ATTREQ_RESTORE_DATABASE="$restore_database" postgres sh -c \
    'createdb -U "$POSTGRES_USER" "$ATTREQ_RESTORE_DATABASE"'
  gzip -dc "$dump" | compose exec -T -e ATTREQ_RESTORE_DATABASE="$restore_database" postgres \
    sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$ATTREQ_RESTORE_DATABASE"'
  printf 'isolated restore completed from %s into database %s\n' "$dump" "$restore_database"
}

rollback() {
  require_docker
  require_env_file
  local image="${1:-}"
  [[ -n "$image" ]] || die "rollback requires an existing backend image tag"
  [[ "$image" != *[[:space:]]* ]] || die "backend image tag must not contain whitespace"
  docker image inspect "$image" >/dev/null 2>&1 || die "backend image is not present locally: $image"
  ATTREQ_API_IMAGE="$image" ATTREQ_ENV_FILE="$ENV_FILE" ATTREQ_DATA_DIR="$DATA_DIR" \
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --no-build
  printf 'recreated stack with backend image %s; verify migrations and health before declaring rollback complete.\n' "$image"
}

down() {
  require_docker
  require_env_file
  compose down
  printf 'containers stopped; bind-mounted data under %s was preserved.\n' "$DATA_DIR"
}

command="${1:-}"
case "$command" in
  validate) validate ;;
  init-dirs) init_dirs ;;
  up) up ;;
  status) status ;;
  logs) shift; logs "$@" ;;
  backup) backup ;;
  restore) shift; restore "$@" ;;
  rollback) shift; rollback "$@" ;;
  down) down ;;
  -h|--help|help|'') usage ;;
  *) die "unknown command: $command (run '$0 --help')" ;;
esac
