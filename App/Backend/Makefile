# Makefile for ATTREQ Backend Docker Operations

.PHONY: help build up down restart logs shell migrate test clean lint format lint-check lint-fix format-check quality docker-lint docker-lint-fix docker-format docker-format-check

# Default target
help:
	@echo "ATTREQ Backend Docker Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start development environment"
	@echo "  make dev-build    - Build and start development environment"
	@echo "  make dev-down     - Stop development environment"
	@echo "  make dev-logs     - Show development logs"
	@echo "  make dev-shell    - Open shell in backend container"
	@echo ""
	@echo "Production:"
	@echo "  make prod         - Start production environment"
	@echo "  make prod-build   - Build and start production environment"
	@echo "  make prod-down    - Stop production environment"
	@echo "  make prod-logs    - Show production logs"
	@echo ""
	@echo "Database:"
	@echo "  make migrate      - Run database migrations"
	@echo "  make migrate-new  - Create new migration"
	@echo "  make db-shell     - Open PostgreSQL shell"
	@echo ""
	@echo "Utilities:"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Clean up containers and volumes"
	@echo "  make logs         - Show logs for all services"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint         - Run Ruff linter and show issues"
	@echo "  make lint-fix     - Run Ruff linter and auto-fix issues"
	@echo "  make format       - Format code with Ruff"
	@echo "  make format-check - Check code formatting without changes"
	@echo "  make quality      - Run both linting and formatting checks"

# Development commands
dev:
	docker-compose up -d

dev-build:
	docker-compose up -d --build

dev-down:
	docker-compose down

dev-logs:
	docker-compose logs -f

dev-shell:
	docker-compose exec backend bash

# Production commands
prod:
	docker-compose -f docker-compose.prod.yml up -d

prod-build:
	docker-compose -f docker-compose.prod.yml up -d --build

prod-down:
	docker-compose -f docker-compose.prod.yml down

prod-logs:
	docker-compose -f docker-compose.prod.yml logs -f

# Database commands
migrate:
	docker-compose exec backend alembic upgrade head

migrate-new:
	@read -p "Migration message: " msg; \
	docker-compose exec backend alembic revision --autogenerate -m "$$msg"

db-shell:
	docker-compose exec postgres psql -U attreq_user -d attreq_db

# Utility commands
test:
	docker-compose exec backend pytest

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	docker system prune -f

# Code Quality commands
lint:
	@echo "Running Ruff linter..."
	ruff check app/ tests/

lint-fix:
	@echo "Running Ruff linter with auto-fix..."
	ruff check app/ tests/ --fix

format:
	@echo "Formatting code with Ruff..."
	ruff format app/ tests/

format-check:
	@echo "Checking code formatting..."
	ruff format app/ tests/ --check

quality: lint-check format-check
	@echo "✅ All code quality checks passed!"

lint-check:
	@echo "Running linter checks..."
	ruff check app/ tests/

# Docker-based code quality commands
docker-lint:
	docker-compose exec backend ruff check app/ tests/

docker-lint-fix:
	docker-compose exec backend ruff check app/ tests/ --fix

docker-format:
	docker-compose exec backend ruff format app/ tests/

docker-format-check:
	docker-compose exec backend ruff format app/ tests/ --check

# Quick start for development
start: dev-build migrate
	@echo "ATTREQ Backend is running at http://localhost:8000"
	@echo "API Documentation: http://localhost:8000/docs"
	@echo "Health Check: http://localhost:8000/health"
