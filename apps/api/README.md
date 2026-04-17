# ATTREQ API

The backend now follows a production-style `src` layout.

## Structure

```text
apps/api/
├── src/attreq_api/
│   ├── api/
│   ├── config/
│   ├── crud/
│   ├── integrations/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── workers/
├── alembic/
├── tests/
└── uploads/
```

## Run Locally

```bash
cd apps/api
cp .env.example .env
PYTHONPATH=src uvicorn attreq_api.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker

Use the root compose files in `infra/docker/`:

```bash
docker compose -f infra/docker/compose.api.yml up -d --build
```
