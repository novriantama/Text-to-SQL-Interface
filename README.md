# Text-to-SQL Interface with Guardrails & Hallucination Detection

A production-grade natural language interface that translates plain English questions into SQL queries, executes them safely using AST guardrails and read-only database sandboxes, detects semantic hallucinations, and presents results with a composite confidence score.

Designed following **Clean Architecture** and **Clean Code** principles.

---

## 🏗️ Project Architecture

```
src/
├── core/                  # Application configuration, logger, container, base exceptions
├── domain/                # Layer 1: Entities, domain exceptions, abstract ports (DB, LLM, Guardrails, Validation)
├── application/           # Layer 2: Use cases (Pipeline, Schema Extract, Evals, Feedback) and DTOs
├── infrastructure/        # Layer 3: Adapters (SQLAlchemy, DuckDB, instructor, sqlparse AST, back-translation, vector retriever)
└── presentation/          # Layer 4: FastAPI REST server (v1) and Streamlit dashboard
```

---

## 🚀 Quickstart Guide

### 1. Install Dependencies
```bash
make install
# or for development
make dev
```

### 2. Environment Setup
Copy the `.env.example` file to `.env` and fill in your LLM API keys:
```bash
cp .env.example .env
```

### 3. Run Tests
```bash
make test
```

### 4. Run API Server (FastAPI)
```bash
make run-api
```
Access interactive OpenAPI documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

### 5. Run UI Dashboard (Streamlit)
```bash
make run-ui
```
Access Streamlit dashboard at [http://localhost:8501](http://localhost:8501).

### 6. Run with Docker Compose
```bash
docker-compose up --build
```