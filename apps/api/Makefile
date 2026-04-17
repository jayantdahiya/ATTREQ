COMPOSE_DEV := ../../infra/docker/compose.api.yml
COMPOSE_PROD := ../../infra/docker/compose.api.prod.yml
PYTHON_BIN := ../../.venv/bin/python
PYTEST_BIN := ../../.venv/bin/pytest
RUFF_BIN := ../../.venv/bin/ruff
UVICORN_BIN := ../../.venv/bin/uvicorn

.PHONY: help dev test lint format compose-up compose-down compose-logs migrate

help:
	@echo "ATTREQ API commands"
	@echo "Use the root Makefile for the canonical monorepo entrypoint."

dev:
	PYTHONPATH=src $(UVICORN_BIN) attreq_api.main:app --reload --host 0.0.0.0 --port 8000

test:
	PYTHONPATH=src $(PYTEST_BIN)

lint:
	$(RUFF_BIN) check src tests

format:
	$(RUFF_BIN) format src tests

compose-up:
	docker compose -f $(COMPOSE_DEV) up -d --build

compose-down:
	docker compose -f $(COMPOSE_DEV) down

compose-logs:
	docker compose -f $(COMPOSE_DEV) logs -f

migrate:
	PYTHONPATH=src $(PYTHON_BIN) -m alembic upgrade head
