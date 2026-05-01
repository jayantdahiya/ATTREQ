COMPOSE_DEV := infra/docker/compose.api.yml
COMPOSE_LOCAL := infra/docker/compose.api.dev.yml
COMPOSE_PROD := infra/docker/compose.api.prod.yml
ENV_FILE := --env-file .env
PYTHON_BIN := .venv/bin/python

.PHONY: help dev dev-api dev-landing dev-web dev-mobile build build-web test lint format compose-up compose-down compose-logs compose-local-up compose-prod-up compose-prod-down api-shell migrate clean

help:
	@echo "ATTREQ monorepo commands"
	@echo ""
	@echo "  make dev             Start API stack and web dev server"
	@echo "  make dev-api         Start backend app locally"
	@echo "  make dev-landing     Start landing app locally"
	@echo "  make dev-web         Start frontend app locally"
	@echo "  make dev-mobile      Start the Expo mobile app"
	@echo "  make build           Build frontend and verify backend imports"
	@echo "  make test            Run backend tests"
	@echo "  make lint            Run backend Ruff and frontend lint"
	@echo "  make format          Format backend code"
	@echo "  make compose-up      Start full API stack via Docker Compose"
	@echo "  make compose-down    Stop full API stack"
	@echo "  make compose-logs    Follow API stack logs"
	@echo "  make compose-local-up Start local DB/cache dependencies only"
	@echo "  make compose-prod-up Start production compose stack"
	@echo "  make compose-prod-down Stop production compose stack"

dev:
	@echo "Run \`make compose-up\` in one terminal and \`make dev-web\` in another."

dev-api:
	cd apps/api && PYTHONPATH=src ../../$(PYTHON_BIN) -m uvicorn attreq_api.main:app --reload --host 0.0.0.0 --port 8000

dev-landing:
	cd apps/landing && npm run dev

dev-web:
	cd apps/web && npm run dev

dev-mobile:
	cd apps/mobile && npm run start

build: build-web
	cd apps/api && PYTHONPATH=src ../../$(PYTHON_BIN) -c "from attreq_api.main import app; print(app.title)"

build-web:
	cd apps/web && npm run build

test:
	cd apps/api && PYTHONPATH=src ../../$(PYTHON_BIN) -m pytest

lint:
	cd apps/api && ../../$(PYTHON_BIN) -m ruff check src tests
	cd apps/web && npm run lint

format:
	cd apps/api && ../../$(PYTHON_BIN) -m ruff format src tests

compose-up:
	docker compose -f $(COMPOSE_DEV) $(ENV_FILE) up -d --build

compose-down:
	docker compose -f $(COMPOSE_DEV) $(ENV_FILE) down

compose-logs:
	docker compose -f $(COMPOSE_DEV) $(ENV_FILE) logs -f

compose-local-up:
	docker compose -f $(COMPOSE_LOCAL) up -d

compose-prod-up:
	docker compose -f $(COMPOSE_PROD) up -d --build

compose-prod-down:
	docker compose -f $(COMPOSE_PROD) down

api-shell:
	cd apps/api && PYTHONPATH=src ../../$(PYTHON_BIN)

migrate:
	cd apps/api && PYTHONPATH=src ../../$(PYTHON_BIN) -m alembic upgrade head

clean:
	find . -name ".DS_Store" -delete
