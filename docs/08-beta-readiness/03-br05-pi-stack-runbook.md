# BR-05 — Raspberry Pi Beta Stack Runbook

> Status: repository preparation complete; do not operate this runbook until the Pi-change permission and BR-04 component decision are recorded in `00-immediate-beta-readiness.md`.
>
> Scope: a private Raspberry Pi 5 stack with no host-published backend, database, cache, or vector-service ports. Cloudflare Tunnel is the only intended ingress.

## What this deploys

`infra/docker/compose.pi-beta.yml` starts PostgreSQL 15, Redis 7, a one-shot Alembic migration service, the FastAPI backend, and `cloudflared`. All communicate on a private Docker bridge network. The Pi opens an outbound tunnel connection; do not create router port-forwarding rules.

Persistent bind mounts are below `${ATTREQ_DATA_DIR:-/mnt/storage/attreq}`:

| Directory | Purpose |
| --- | --- |
| `postgres/` | PostgreSQL database cluster; ownership is resolved from the pinned image at first creation |
| `redis/` | Redis append-only persistence |
| `uploads/` | Local fallback images only; BR-07 should move beta images to private R2 |
| `backups/` | Compressed PostgreSQL dump files before off-Pi copy |
| `weaviate/`, `transformer-cache/` | Created but unused unless the BR-04 vectors decision passes |
| `secrets/pi-beta.env` | Pi-only environment file, never committed |

`EMBEDDINGS_ENABLED=false` and `RERANKER_ENABLED=false` are the default beta posture. `EMBEDDINGS_ENABLED` controls FashionCLIP inference in the backend and has its own BR-04 decision; it can be enabled independently only after its measured memory/load behavior is acceptable. The optional `weaviate` profile starts Weaviate for manual vectors. The separate `text2vec` profile starts only the transformer sidecar; semantic text vectorization requires both profiles plus the documented Weaviate module settings. The remote reranker can be enabled independently after its own BR-04 decision.

## Prerequisites and decisions

1. Explicit user approval to install Docker, Docker Compose, and `cloudflared` image on the Pi and create `/mnt/storage/attreq`.
2. A current Docker Engine and Compose plugin installed for the Pi's ARM64 Ubuntu release, following the official Docker instructions current on the installation day.
3. A named Cloudflare Tunnel and chosen hostname from BR-06. Do not migrate `dev-server-1.online` from the Mac until Pi health is ready.
4. Unique production values for database password and `SECRET_KEY` (at least 32 characters), the selected classifier credential, OpenWeather key, and tunnel token. Never paste them into chat or Git.
5. The BR-04 decision for FashionCLIP, Weaviate, `text2vec-transformers`, and the reranker. The minimal stack does not require any of them.
6. BR-07 decisions for private R2 bucket, off-Pi backup destination, Sentry DSN, and external HTTPS monitor before inviting testers.

## Initial Pi setup

Clone a reviewed commit/tag on the Pi, then keep secrets outside that checkout:

```bash
git clone <your-ATTREQ-repository> /opt/attreq
cd /opt/attreq
git checkout <reviewed-commit-or-tag>

sudo install -d -m 0750 /mnt/storage/attreq/secrets
sudo install -m 0600 infra/docker/.env.pi-beta.example \
  /mnt/storage/attreq/secrets/pi-beta.env
sudo chown "$USER":"$USER" /mnt/storage/attreq/secrets/pi-beta.env
chmod 600 /mnt/storage/attreq/secrets/pi-beta.env
```

Edit the external file with a local editor. It must contain real values for `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `SECRET_KEY`, `TUNNEL_TOKEN`, `TRUSTED_HOSTS`, `BACKEND_CORS_ORIGINS`, `CLASSIFIER_PROVIDER`, its matching API key, and `OPENWEATHER_API_KEY`.

For the initial minimal beta, set at least:

```dotenv
STORAGE_BACKEND=local
RATE_LIMIT_ENABLED=true
RATE_LIMIT_TRUST_PROXY_HEADERS=true
EMBEDDINGS_ENABLED=false
RERANKER_ENABLED=false
```

`STORAGE_BACKEND=local` is temporary until BR-07 verifies private R2. The mounted `uploads/` directory is durable across backend container replacement but is not an off-Pi backup.

Export the environment-file location before every operator command:

```bash
cd /opt/attreq
export ATTREQ_ENV_FILE=/mnt/storage/attreq/secrets/pi-beta.env
export ATTREQ_DATA_DIR=/mnt/storage/attreq
# Optional for a retained, rollback-capable local backend image:
export ATTREQ_API_IMAGE=attreq-api:beta
```

Create the SSD directories without deleting existing data, then validate the resolved Compose configuration:

```bash
scripts/dev/pi-beta.sh init-dirs
scripts/dev/pi-beta.sh validate
```

`init-dirs` deliberately refuses to chown an existing PostgreSQL directory. Stop and inspect ownership instead of trying to repair it blindly.

## Trusted proxy CIDR

The rate limiter uses forwarded Cloudflare client-IP headers only when the immediate peer is allowlisted. Since `cloudflared` and `backend` share the Compose network, discover that bridge network CIDR after `docker compose config` succeeds:

```bash
docker network inspect attreq-beta_internal \
  --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}'
```

Set the resulting narrow subnet as a JSON list in the external secret file, for example:

```dotenv
RATE_LIMIT_TRUSTED_PROXY_CIDRS=["172.29.0.0/16"]
```

Do not copy that example CIDR blindly. Do not enable proxy-header trust if traffic can reach `backend` other than through the local `cloudflared` service.

## Start, migrations, and health

The `migrations` service runs `alembic upgrade head` only after PostgreSQL health succeeds. The backend will not start unless migrations completed successfully. There are no blind startup sleeps.

```bash
scripts/dev/pi-beta.sh up
scripts/dev/pi-beta.sh status
scripts/dev/pi-beta.sh logs cloudflared
```

Expected health response includes `"environment":"production"`; this enables the production trusted-host policy for the beta deployment. Ensure `TRUSTED_HOSTS` includes the chosen public hostname plus `backend` and `localhost` for internal tunnel/health requests. Confirm the migration container exit code is zero and Cloudflare tunnel logs show a connected registration:

```bash
docker compose --env-file "$ATTREQ_ENV_FILE" \
  -f infra/docker/compose.pi-beta.yml ps
docker compose --env-file "$ATTREQ_ENV_FILE" \
  -f infra/docker/compose.pi-beta.yml logs --tail=100 migrations cloudflared
```

BR-06 then configures the named tunnel's public hostname to route to `http://backend:8000` in this stack. Verify from mobile data only after the hostname is switched:

```bash
curl -fsS https://<chosen-beta-hostname>/health
```

The response must be HTTP 200 and must not report `development`. Stopping the Mac backend must have no effect on that hostname.

## Optional components (only after BR-04)

Keep every feature flag and profile off by default. Apply only the measured combinations below.

If FashionCLIP and manual-vector Weaviate pass, set `EMBEDDINGS_ENABLED=true`, leave the Weaviate vectorizer/module variables empty, and start Weaviate independently:

```bash
docker compose --env-file "$ATTREQ_ENV_FILE" \
  -f infra/docker/compose.pi-beta.yml --profile weaviate up -d --build
docker compose --env-file "$ATTREQ_ENV_FILE" \
  -f infra/docker/compose.pi-beta.yml restart backend
```

If legacy semantic text search and its transformer both pass, set these Pi-only Compose values and start both independently gated profiles:

```dotenv
WEAVIATE_DEFAULT_VECTORIZER_MODULE=text2vec-transformers
WEAVIATE_ENABLE_MODULES=text2vec-transformers,backup-filesystem
```

```bash
docker compose --env-file "$ATTREQ_ENV_FILE" \
  -f infra/docker/compose.pi-beta.yml \
  --profile weaviate --profile text2vec up -d --build
docker compose --env-file "$ATTREQ_ENV_FILE" \
  -f infra/docker/compose.pi-beta.yml restart backend
```

Restarting the backend after Weaviate is healthy is required because its current client connects during module import and does not reconnect automatically. Check `docker stats` and API health/recommendation latency at the BR-04 load level before retaining either profile. If only the remote reranker passed, set `RERANKER_ENABLED=true` and leave both local profiles and `EMBEDDINGS_ENABLED` off.

## Backup and restore

Create a PostgreSQL dump without exposing database ports:

```bash
scripts/dev/pi-beta.sh backup
ls -lh /mnt/storage/attreq/backups/
```

The SSD is not a backup destination by itself. BR-07 must schedule an encrypted/off-Pi copy with retention and rehearse an isolated restore. For an explicit restore drill, first take a fresh backup and identify exactly one compressed SQL dump. The script refuses to touch the live database: it starts PostgreSQL if required, creates a new named database only when it does not already exist, and restores there. The backend remains running.

```bash
scripts/dev/pi-beta.sh backup
ATTREQ_RESTORE_DATABASE=attreq_restore_20260812 \
ATTREQ_CONFIRM_RESTORE=RESTORE \
  scripts/dev/pi-beta.sh restore /mnt/storage/attreq/backups/<exact-dump>.sql.gz
docker compose --env-file "$ATTREQ_ENV_FILE" \
  -f infra/docker/compose.pi-beta.yml exec postgres \
  sh -c 'psql -U "$POSTGRES_USER" -d attreq_restore_20260812 -c "\\dt"'
```

`restore` requires an explicit existing `.sql.gz` file, a valid `ATTREQ_RESTORE_DATABASE` distinct from the live database, and the confirmation variable. It refuses an existing target database and does not delete Docker volumes. BR-07 must verify the restored isolated database and then define its off-Pi retention policy.

## Reboot and routine operations

The services use `restart: unless-stopped`; after a planned Pi reboot, verify rather than assuming recovery:

```bash
sudo reboot
# reconnect after the Pi is reachable
cd /opt/attreq
export ATTREQ_ENV_FILE=/mnt/storage/attreq/secrets/pi-beta.env
scripts/dev/pi-beta.sh status
scripts/dev/pi-beta.sh logs cloudflared
```

Compose log rotation retains three 10 MB local log files per service. Watch both `/mnt/storage` and the microSD root filesystem; BR-07 adds monitoring and alerting.

## Safe rollback

Before a code deploy, preserve a successful database backup and record both the current Git commit and backend image tag:

```bash
scripts/dev/pi-beta.sh backup
git rev-parse HEAD
docker image ls attreq-api
```

For an application-only regression with a compatible schema, recreate the stack from an already-present previous backend image:

```bash
scripts/dev/pi-beta.sh rollback attreq-api:<previous-reviewed-tag>
scripts/dev/pi-beta.sh status
```

For a source checkout rollback, check out the previous reviewed Git tag, set `ATTREQ_API_IMAGE` to a distinct prior tag, build it intentionally, and use the same Compose file. Do not use `git reset --hard`, `docker compose down --volumes`, or deletion of bind mounts as a rollback shortcut. If a migration is incompatible, stop and use the BR-07 isolated restore procedure to investigate/rehearse recovery before performing any planned production recovery.

To stop the stack while preserving all data:

```bash
scripts/dev/pi-beta.sh down
```

## Remaining decisions for BR-06 and BR-07

- BR-06: choose whether to migrate `dev-server-1.online` or create `api.<owned-domain>`, create/configure the named tunnel token, route the DNS hostname, and test outside the home network.
- BR-07: approve private R2 and configure its S3 credentials, choose an off-Pi encrypted backup target/retention, configure Sentry and an external `/health` monitor, and perform a real isolated restore drill.
- Before Android BR-08, choose the durable backup location for the upload/release keystore and GitHub release visibility.
