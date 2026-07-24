.PHONY: help install dev test eval lint format run-api run-ui run-frontend docker-build docker-up docker-down docker-logs

help:
	@echo "Available commands:"
	@echo "  install      Install all Python dependencies"
	@echo "  dev          Install development dependencies"
	@echo "  test         Run unit and integration test suite"
	@echo "  eval         Run 52-case automated evaluation benchmark runner"
	@echo "  lint         Run ruff and mypy linters"
	@echo "  format       Format code with black and ruff"
	@echo "  run-api      Run FastAPI server on port 8000"
	@echo "  run-frontend Run Vite React frontend on port 3000"
	@echo "  docker-build Build all Docker containers (Postgres, API, Frontend)"
	@echo "  docker-up    Start full containerized stack with seeded database"
	@echo "  docker-down  Stop Docker containers"

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	python3 -m unittest discover -s tests -p "test_*.py"

eval:
	PYTHONPATH=. python3 scripts/run_evals.py

lint:
	ruff check src/ tests/
	mypy src/

format:
	black src/ tests/
	ruff check --fix src/ tests/

run-api:
	uvicorn src.presentation.api.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	cd frontend && npm run dev

docker-build:
	docker compose build

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f
