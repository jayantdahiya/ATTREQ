# ATTREQ Raspberry Pi microSD Beta Deployment

> **Purpose:** Run the invite-only backend on the Pi's system microSD while user images remain in private Cloudflare R2.
> **Scope:** Temporary beta topology only. Move PostgreSQL to reliable SSD/NVMe storage before expanding the tester group.
> **Safety invariant:** Never restore over the live database. Never expose port 8000 on the router. Never put a secret in Git or a shell transcript.

## Architecture and accepted trade-offs

The microSD stores PostgreSQL and bounded container logs. Redis and the local upload path use tmpfs, so Redis cache/rate-limit counters reset after a restart and accidental local upload scratch data is disposable. The API sets `STORAGE_BACKEND=s3`; originals, processed images, thumbnails, and Style DNA images therefore remain in the existing private R2 bucket.

```text
dev-server-1.online -> Cloudflare Tunnel -> FastAPI
                                           |-- PostgreSQL: /var/lib/attreq/postgres
                                           |-- Redis: RAM only (no AOF/RDB)
                                           |-- upload scratch: RAM only
                                           `-- user images: private R2

PostgreSQL -> gzip staging -> verified R2 object
             /var/lib/attreq/backups   attreq-db-backups/postgres/...
```

This topology intentionally keeps FashionCLIP/Weaviate and the Groq reranker off for the initial stability soak. Do not start the optional Compose profiles until a separate load gate approves them.

## Files

- `infra/docker/compose.pi-beta.yml`: common Pi beta stack.
- `infra/docker/compose.pi-microsd.yml`: required microSD overlay.
- `scripts/dev/pi-microsd-backup.py`: dump, upload, integrity verification, retention, download, and isolated restore tool.
- `/etc/attreq/pi-beta.env`: external mode-`0600` secret environment file; never copy it into the repository.
- `/var/lib/attreq`: microSD data root.

All commands below run from `/opt/attreq` on the Pi.

## 1. Pre-deployment gates

Do not start if any gate fails:

1. The Pi is on reliable power and wired Ethernet.
2. Root has at least 8 GiB free, no more than 75% used, and at least 100,000 free inodes.
3. `dmesg` contains no current `mmc`, EXT4, I/O, undervoltage, or filesystem errors.
4. The old Mac backend and its tunnel route remain available for at least 48 hours after cutover.
5. The Pi checkout is the reviewed `main` commit intended for deployment.
6. The private R2 bucket and scoped Object Read/Write credentials have passed a create/read/delete probe.
7. A valid Groq credential and all required production settings are in the external environment file.

Run the read-only checks:

```bash
cd /opt/attreq
git status --short
git rev-parse HEAD
df -h /
df -i /
free -h
docker version
docker compose version
sudo dmesg --level=err,warn | tail -n 100
```

Stop if the checkout is dirty or its commit is not the intended release. Do not use `git reset --hard`, `docker system prune`, or automatic image/volume pruning as a cleanup shortcut.

## 2. Prepare the microSD directories

Export the operator paths in every deployment shell:

```bash
export ATTREQ_DATA_DIR=/var/lib/attreq
export ATTREQ_ENV_FILE=/etc/attreq/pi-beta.env
```

Initialize bind mounts using the existing ownership-aware helper, then make backup staging private and writable by the current operator:

```bash
cd /opt/attreq
scripts/dev/pi-beta.sh init-dirs
sudo install -d -m 0700 -o "$(id -u)" -g "$(id -g)" \
  /var/lib/attreq/backups /var/lib/attreq/restores
sudo test -d /var/lib/attreq/postgres
sudo test -d /var/lib/attreq/backups
```

`redis/` and `uploads/` may exist from the common helper, but the microSD overlay replaces both container mounts with tmpfs. They should not receive runtime writes in this topology.

Do not configure a disk-backed swapfile on the microSD. Existing zram is acceptable. If a disk swapfile already exists, inspect it before changing the host; do not delete it blindly.

## 3. Populate the external environment file

Create `/etc/attreq/pi-beta.env` as root and make it mode `0600`. Reuse the already configured task credentials without printing them:

```bash
sudo install -d -m 0750 /etc/attreq
sudo test -f /etc/attreq/pi-beta.env
sudo chmod 0600 /etc/attreq/pi-beta.env
sudo stat -c '%a %n' /etc/attreq/pi-beta.env
```

The file must contain the production database/JWT/tunnel/provider settings from `.env.pi-beta.example` plus these R2 settings:

```dotenv
STORAGE_BACKEND=s3
S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
S3_BUCKET=<existing-private-bucket>
S3_ACCESS_KEY_ID=<scoped-object-read-write-id>
S3_SECRET_ACCESS_KEY=<scoped-object-read-write-secret>

EMBEDDINGS_ENABLED=false
RERANKER_ENABLED=false

# Replace this CIDR with the exact `attreq-beta_internal` subnet reported by
# `docker network inspect` after first start. JSON syntax is required here.
RATE_LIMIT_TRUST_PROXY_HEADERS=true
RATE_LIMIT_TRUSTED_PROXY_CIDRS=["172.19.0.0/16"]
```

Do not add `ATTREQ_DATA_DIR` or `ATTREQ_ENV_FILE` to this file; they are non-secret operator exports. Do not add a public R2 URL or make the bucket public. The application stores object keys in PostgreSQL and returns time-limited presigned URLs.

## 4. Validate the merged Compose model

Every command must include both Compose files in this order:

```bash
cd /opt/attreq
export ATTREQ_DATA_DIR=/var/lib/attreq
export ATTREQ_ENV_FILE=/etc/attreq/pi-beta.env

pi_compose() {
  docker compose --env-file "$ATTREQ_ENV_FILE" \
    -f infra/docker/compose.pi-beta.yml \
    -f infra/docker/compose.pi-microsd.yml "$@"
}

pi_compose config --quiet
pi_compose config | sed -n '/redis:/,/^[^ ]/p' | grep -E -- '--appendonly|--save|type: tmpfs'
pi_compose config | sed -n '/backend:/,/^[^ ]/p' | grep -E 'STORAGE_BACKEND: s3|target: /app/uploads|type: tmpfs'
```

Expected invariants:

- Redis command contains `--appendonly no --save ""`.
- Redis `/data` is a 64 MiB tmpfs; there is no persistent `/data` bind in the resolved service.
- Backend `/app/uploads` is a 256 MiB tmpfs.
- Backend and migrations resolve `STORAGE_BACKEND: s3`.
- PostgreSQL still binds `/var/lib/attreq/postgres`.
- The backend sees `/var/lib/attreq/backups` read-only for R2 upload verification.
- No service publishes a host port.

## 5. Start the private stack

The one-shot `storage-guard` runs before PostgreSQL. It refuses startup when root usage exceeds 75%, free space is below 8 GiB, or fewer than 100,000 inodes remain.

```bash
pi_compose up -d --build
pi_compose ps
pi_compose logs --no-color storage-guard migrations
pi_compose exec -T backend curl --fail --silent --show-error http://localhost:8000/health
```

Expected results:

- `storage-guard` exits `0` with a passed message.
- PostgreSQL and Redis are healthy.
- `migrations` exits `0`.
- Backend and cloudflared are healthy/running.
- Health reports `production`, never `development`.

After first start, obtain the actual bridge subnet and place that exact JSON
list in the external environment file before recreating the backend:

```bash
docker network inspect attreq-beta_internal \
  --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}'
```

Do not copy the example CIDR blindly. Proxy headers remain untrusted unless the
immediate peer belongs to this allowlist.

Confirm the write-minimizing mounts:

```bash
pi_compose exec -T redis redis-cli CONFIG GET appendonly
pi_compose exec -T redis redis-cli CONFIG GET save
pi_compose exec -T redis sh -ec 'mount | grep "on /data "'
pi_compose exec -T backend sh -ec 'mount | grep "on /app/uploads "'
```

`appendonly` must be `no`, `save` must be empty, and both mounts must report tmpfs.

## 6. Verify R2 before hostname cutover

Use a new beta account and non-sensitive test image while the Pi tunnel is not yet the public route:

1. Register and log in.
2. Upload one wardrobe image.
3. Wait for classification, processed image, and thumbnail generation.
4. Read the item again and confirm its presigned image renders.
5. Restart the backend container and confirm the image still renders.
6. Delete the test item and confirm the matching R2 object is removed.

Also confirm no image appeared in the local persistent fallback directory:

```bash
sudo du -sh /var/lib/attreq/uploads
```

Do not cut over if any R2 operation fails. A successful `/health` response alone does not prove image durability.

## 7. Create and verify an off-Pi database backup

The backup tool uses PostgreSQL and boto3 inside the existing containers, so the Pi host needs no database client, AWS CLI, or R2 secret in its process arguments. It never stages uncompressed SQL.

Run its offline tests and non-mutating plan first:

```bash
scripts/dev/pi-microsd-backup.py self-test
scripts/dev/pi-microsd-backup.py backup --dry-run
```

Create the real backup:

```bash
scripts/dev/pi-microsd-backup.py backup
```

The tool:

1. Streams `pg_dump` into a mode-private `.sql.gz.partial` file.
2. Flushes and atomically renames the completed gzip.
3. Validates the gzip and calculates SHA-256.
4. Uploads to a unique UTC key such as `attreq-db-backups/postgres/2026/08/14/attreq-postgres-20260814T120000Z-<nonce>.sql.gz`.
5. Downloads the uploaded bytes inside the backend container and verifies their SHA-256 and size.
6. Records SHA-256, format, kind, and creation time as R2 object metadata.
7. Applies retention only to recognized ATTREQ objects below `attreq-db-backups/postgres/`.
8. Removes local staging only after upload, integrity verification, and retention succeed.

Unknown objects, objects without ATTREQ metadata, and everything outside that dedicated prefix are never deleted. Retention keeps the newest snapshot for seven distinct UTC days and the newest snapshot for four distinct ISO weeks; one object may satisfy both windows. Extra intra-day snapshots are deleted after a newer verified backup exists.

Preview retention without deleting:

```bash
scripts/dev/pi-microsd-backup.py prune --dry-run
```

Use `backup --keep-local` only for a deliberate restore drill; routine backups should leave the verified copy in R2 and avoid consuming microSD space.

### Six-hour schedule

Install the tracked systemd service and timer, then verify the resolved calendar:

```bash
sudo install -m 0644 infra/systemd/attreq-db-backup.service \
  /etc/systemd/system/attreq-db-backup.service
sudo install -m 0644 infra/systemd/attreq-db-backup.timer \
  /etc/systemd/system/attreq-db-backup.timer
sudo systemctl daemon-reload
sudo systemctl enable --now attreq-db-backup.timer
systemctl list-timers attreq-db-backup.timer --all
systemd-analyze calendar '*-*-* 00/6:17:00 UTC'
```

The timer runs at minute 17 every six UTC hours, catches a missed invocation
after reboot, and writes to the bounded system journal. Inspect each run with:

```bash
systemctl status attreq-db-backup.service --no-pager
journalctl -u attreq-db-backup.service --since '24 hours ago' --no-pager
```

Treat a failed unit or missing verified backup for more than six hours as a deployment rollback trigger.

## 8. Perform the mandatory isolated restore drill

Choose one exact key printed by a successful backup. Download refuses keys outside the dedicated prefix and refuses to overwrite a local file:

```bash
BACKUP_KEY='attreq-db-backups/postgres/YYYY/MM/DD/attreq-postgres-YYYYMMDDTHHMMSSZ-<nonce>.sql.gz'
RESTORE_FILE="/var/lib/attreq/restores/$(basename "$BACKUP_KEY")"

scripts/dev/pi-microsd-backup.py download "$BACKUP_KEY" --output "$RESTORE_FILE" --dry-run
scripts/dev/pi-microsd-backup.py download "$BACKUP_KEY" --output "$RESTORE_FILE"
```

Restore only into a new database name. The command refuses the live database name and fails when the target already exists; it never drops or truncates any database:

```bash
RESTORE_DATABASE="attreq_restore_$(date -u +%Y%m%dT%H%M%SZ)"
scripts/dev/pi-microsd-backup.py restore-isolated "$RESTORE_FILE" \
  --database "$RESTORE_DATABASE" \
  --confirm-isolated-restore
```

Verify representative tables and counts against the isolated database:

```bash
pi_compose exec -T -e ATTREQ_RESTORE_DATABASE="$RESTORE_DATABASE" postgres \
  sh -ec 'psql -U "$POSTGRES_USER" -d "$ATTREQ_RESTORE_DATABASE" -c "\\dt"'
pi_compose exec -T -e ATTREQ_RESTORE_DATABASE="$RESTORE_DATABASE" postgres \
  sh -ec 'psql -U "$POSTGRES_USER" -d "$ATTREQ_RESTORE_DATABASE" -c "SELECT COUNT(*) FROM users;"'
```

The two shell variables above contain no secret. `POSTGRES_USER` is expanded only inside the container; do not print or source the secret env file merely to run the check.

The backup tool deliberately leaves the isolated database and downloaded dump for inspection. After acceptance, remove them only with a separate reviewed operator action. Never automate `dropdb` in the backup schedule.

## 9. Cut over and soak

Only after private health, the full R2 flow, a verified backup, and the isolated restore all pass:

1. Point `dev-server-1.online` to the `attreq-pi-beta` named tunnel.
2. Confirm `https://dev-server-1.online/health` reports production.
3. Stop the Mac development backend temporarily and confirm public health remains green.
4. Run `register -> onboarding -> upload -> classification -> recommendation -> feedback/history` from the signed APK over mobile data.
5. Preserve the old Mac tunnel route as rollback for at least 48 hours.

Monitor during the 48-hour soak:

```bash
watch -n 30 'df -h /; df -i /; docker compose --env-file /etc/attreq/pi-beta.env -f /opt/attreq/infra/docker/compose.pi-beta.yml -f /opt/attreq/infra/docker/compose.pi-microsd.yml ps'
sudo dmesg --follow --level=err,warn
```

Also use an external HTTPS monitor and Sentry; a Pi-local health check cannot detect a failed tunnel or home Internet outage.

## Exact rollback triggers

Route `dev-server-1.online` back to the known-good Mac backend immediately when any trigger occurs:

- public `/health` fails twice consecutively one minute apart;
- HTTP 5xx exceeds 2% for five consecutive minutes;
- API p95 latency exceeds 3 seconds for 15 minutes outside a known Groq call;
- registration, authentication, image upload/render, or recommendation generation fails in two consecutive smoke tests;
- root usage exceeds 75%, root free space falls below 8 GiB, or fewer than 100,000 free inodes remain;
- `dmesg` reports any new microSD I/O, EXT4, journal, read-only-filesystem, or undervoltage error;
- PostgreSQL restarts more than once in 15 minutes or fails its health check;
- no verified R2 database backup completes within six hours, SHA/size verification fails, or the isolated restore drill fails;
- R2 create/read/delete or presigned image rendering fails;
- the tunnel repeatedly reconnects or external monitoring cannot reach it for five minutes.

Rollback sequence:

1. Repoint the Cloudflare hostname to the preserved Mac tunnel route. The APK hostname does not change.
2. Verify public `/health` and one authenticated read against the Mac backend.
3. Stop Pi ingress while preserving its database:

   ```bash
   pi_compose stop cloudflared backend
   pi_compose ps
   ```

4. Capture Pi logs, `df`, container state, and `dmesg`; do not prune or delete data.
5. Diagnose before retrying. Do not reverse Alembic migrations automatically. If a schema change prevents the old application from reading the database, keep traffic on the Mac's known-good data and prepare a reviewed forward fix.
6. Use R2 restore only for confirmed data loss, into an isolated database first. A backup is not a routine application rollback mechanism.

## Completion checklist

- [x] Merged Compose config passes and publishes no host ports.
- [x] Startup storage guard passes at the documented thresholds.
- [x] Redis AOF and snapshots are disabled; Redis `/data` is tmpfs.
- [x] Backend upload scratch is tmpfs and `STORAGE_BACKEND=s3`.
- [x] Full R2 image lifecycle passes across a backend restart.
- [x] First PostgreSQL backup is uploaded and SHA/size verified.
- [x] Retention dry-run touches only recognized objects under the dedicated prefix.
- [x] Download and isolated restore drill pass without modifying the live database.
- [x] Six-hour backup schedule and bounded journal logging are active.
- [ ] External HTTPS monitoring and Sentry are active.
- [ ] Signed APK passes the end-to-end flow over mobile data.
- [x] Mac route is retained for the 48-hour soak.

The microSD deployment milestone is not complete until this runbook's repository changes are committed and pushed under the project milestone policy and the live backup/restore and physical-phone gates pass.
