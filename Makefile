.PHONY: help install dev test lint format run-api run-ui docker-build docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  install      Install all dependencies using pip/editable mode"
	@echo "  dev          Install dev dependencies"
	@echo "  test         Run unit, integration, and evaluation tests"
	@echo "  lint         Run ruff and mypy"
	@echo "  format       Format code with black and ruff"
	@echo "  run-api      Run FastAPI server on port 8000"
	@echo "  run-ui       Run Streamlit UI on port 8501"
	@echo "  docker-up    Start Docker containers"
	@echo "  docker-down  Stop Docker containers"

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=src

lint:
	ruff check src/ tests/
	mypy src/

format:
	black src/ tests/
	ruff check --fix src/ tests/

run-api:
	uvicorn src.presentation.api.main:app --host 0.0.0.0 --port 8000 --reload

run-ui:
	streamlit run src/presentation/ui/app.py --server.port 8501

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down
