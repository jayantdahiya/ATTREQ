# Agents.md — ATTREQ

## Project identity
- **Name:** ATTREQ
- **Purpose:** AI-powered personal stylist app (PWA) that digitizes wardrobe items and generates context-aware outfit recommendations (weather, occasion, history, preferences).
- **Owner context:** Jayant’s **medium-priority** project; target is a strong demo-ready product with real AI workflow quality.

## Primary stack (as implemented)
- **Frontend:** Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, shadcn/ui, Zustand, next-pwa
- **Backend:** FastAPI (Python 3.11+), SQLAlchemy async, Alembic, JWT auth
- **Data:** PostgreSQL, Redis cache, Weaviate vector DB
- **AI/media pipeline:** Roboflow API, rembg, Pillow, scikit-learn, vector similarity with Weaviate
- **Infra:** Docker Compose (dev/prod variants), Makefile workflow

## Repository map
- `App/Backend/` — FastAPI service, migrations, scripts, docker stack
- `App/Frontend/` — Next.js PWA app
- `Extras/` — additional assets and side artifacts
- (README references `Docs/`; validate existence before relying on it)

## Project goals (from code + Jayant memory context)
1. Deliver a reliable **core loop**: upload wardrobe → AI tagging/processing → generate and track outfit suggestions.
2. Build a polished **demo experience** suitable for portfolio/interviews.
3. Improve recommendation quality with explainable scoring and user feedback loops.
4. Keep architecture maintainable as product features grow.

## Near-term roadmap
1. **Demo-first stabilization:** ensure happy path works end-to-end from fresh setup.
2. **Recommendation quality:** tune scoring weights, reduce low-confidence suggestions, improve fallback behavior.
3. **Testing push (Phase 5):** add/expand API integration tests and frontend smoke checks.
4. **User value features:** strengthen outfit history analytics + preference learning signals.
5. **V2 foundations:** prep interfaces for calendar/social/e-commerce integrations without premature complexity.

## Agent operating guidelines
- Prioritize the **user-facing core flow** over peripheral features.
- Do not break compatibility between `App/Frontend` and `App/Backend` API contracts.
- For recommendation changes, include:
  - rationale for scoring logic,
  - test fixtures or reproducible examples,
  - clear fallback behavior when data is sparse.
- Be careful with heavy ML/image dependencies (runtime + container size implications).
- Keep secrets/API keys in env files only; never commit credentials.

## Standard dev/test commands
```bash
# Backend stack
cd App/Backend
cp .env.example .env
docker-compose up -d --build

# Backend quality/tests
make quality
make test

# Frontend
cd ../Frontend
npm install
npm run dev
```

## Definition of done for agent changes
- Core outfit workflow remains functional.
- Backend/Frontend still integrate correctly.
- Tests/lint pass for touched scope.
- README or relevant docs updated for changed behavior.
- Change improves demo readiness, recommendation quality, or maintainability.