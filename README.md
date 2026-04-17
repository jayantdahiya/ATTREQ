# ATTREQ

AI-powered wardrobe management and outfit recommendation platform.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.119-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15-000000?logo=next.js&logoColor=white)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

ATTREQ helps users digitize their wardrobe from photos, organize clothing with AI-generated attributes, and get daily outfit suggestions based on weather, wardrobe history, and user context.

## What It Does

- Upload clothing images and turn them into structured wardrobe items.
- Auto-tag items with AI-assisted classification.
- Generate outfit recommendations from the user’s own wardrobe.
- Use weather and recent wear history to avoid repetitive or unsuitable suggestions.
- Provide a modern web app backed by a FastAPI API and supporting services.

## Tech Stack

### Frontend

- Next.js 15
- React 19
- TypeScript
- Tailwind CSS
- Zustand

### Backend

- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis
- Weaviate

### AI / Processing

- Google Gemini for clothing attribute extraction
- `rembg` for background removal
- Pillow for image processing

## Repository Structure

```text
.
├── apps/
│   ├── api/              # FastAPI backend
│   └── web/              # Next.js frontend
├── docs/                 # Product, implementation, execution, and status docs
├── infra/                # Docker and deployment infrastructure
├── scripts/              # Dev, test, and data scripts
├── assets/               # Design assets
├── research/             # Research and model work
└── packages/             # Shared packages reserved for cross-app code
```

## Quick Start

### 1. Backend

```bash
cd apps/api
cp .env.example .env
PYTHONPATH=src ../../.venv/bin/uvicorn attreq_api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend

```bash
cd apps/web
npm install
npm run dev
```

### 3. Full Local Stack with Docker

```bash
cp apps/api/.env.example apps/api/.env
docker compose -f infra/docker/compose.api.yml up -d --build
```

## Common Commands

The root `Makefile` is the main entrypoint for local development:

```bash
make compose-up
make compose-down
make dev-api
make dev-web
make test
make lint
```

## Documentation

- Start here: [`docs/README.md`](docs/README.md)
- Current project status: [`docs/00-current-status/`](docs/00-current-status/)
- Product overview: [`docs/01-product/`](docs/01-product/)
- Implementation plan: [`docs/02-implementation/plan/`](docs/02-implementation/plan/)

## Current Status

ATTREQ has working backend and frontend foundations, including authentication, wardrobe flows, outfits, and recommendation-related flows. The repository is still under active restructuring and documentation cleanup, so some historical planning docs may describe broader scope than what is currently production-ready.
