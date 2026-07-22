# Clean Architecture & Design System Documentation

## Architecture Overview

This repository is built following **Clean Architecture** principles to create an enterprise-grade Text-to-SQL interface.

```
       +-------------------------------------------------------+
       |   Presentation Layer (FastAPI / Streamlit / CLI)      |
       |  +-------------------------------------------------+  |
       |  | Infrastructure Layer (SQLAlchemy, LLMs, Parsers) |  |
       |  |  +-------------------------------------------+  |  |
       |  |  | Application Layer (Use Cases / Pipeline)  |  |  |
       |  |  |  +-------------------------------------+  |  |  |
       |  |  |  |  Domain Layer (Entities & Ports)   |  |  |  |
       |  |  |  +-------------------------------------+  |  |  |
       |  |  +-------------------------------------------+  |  |
       |  +-------------------------------------------------+  |
       +-------------------------------------------------------+
```

## Layer Specifications

### 1. Domain Layer (`src/domain`)
- **Entities**: Pure Pydantic / Dataclass models representing core concepts (`QueryRequest`, `QueryResponse`, `DatabaseSchema`, `GuardrailResult`, `ConfidenceScore`).
- **Ports**: Abstract Base Classes defining interfaces (`LLMPort`, `DatabasePort`, `GuardrailPort`, `ValidationPort`, `VectorStorePort`).
- **Exceptions**: Custom domain exceptions (`GuardrailViolationException`, `AmbiguousQueryException`).

### 2. Application Layer (`src/application`)
- **Use Cases**: Encapsulates application workflows (`ProcessTextToSQLUseCase`, `ExtractSchemaUseCase`, `EvaluateQueriesUseCase`, `SubmitFeedbackUseCase`).
- **DTOs**: Data Transfer Objects for cross-boundary communication.

### 3. Infrastructure Layer (`src/infrastructure`)
- **DB Adapter**: SQLAlchemy schema reflection and DuckDB/Postgres read-only transaction sandbox execution.
- **Guardrails Adapter**: `sqlparse` AST parsing, DDL/DML blocking, subquery depth limiters, EXPLAIN scan cost calculators.
- **LLM Adapter**: OpenAI & Claude models via `instructor` for structured query generation and back-translation.
- **Validation Adapter**: Hallucination detection via back-translation, result sanity metrics, and multi-query consensus checks.
- **Vector Store Adapter**: Semantic threshold schema retrieval.

### 4. Presentation Layer (`src/presentation`)
- **FastAPI Web API**: Versioned REST endpoints (`/v1/query`, `/v1/schema`, `/v1/feedback`).
- **Streamlit UI**: Interactive dashboard with syntax highlighting, visual confidence gauge, and query history.

### 5. Core Infrastructure (`src/core`)
- Configuration via `pydantic-settings`.
- Structured logging setup.
- Centralized dependency injection container.
