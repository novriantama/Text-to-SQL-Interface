# Text-to-SQL Interface with Guardrails & Hallucination Detection: Complete 14-Day Learning Path

This document details a step-by-step curriculum to master, implement, and deploy a production-grade **Text-to-SQL Interface**. It expands upon the core phases in [Text-to-SQL Interface.md](file:///Users/hafidz/Projects/Text-to-SQL-Interface/docs/Text-to-SQL%20Interface.md), providing the theoretical foundation, coding tasks, architecture layouts, and code templates required to build a portfolio-ready system that compliance and engineering teams would approve.

---

## 🏗️ System Architecture Overview

Before starting, familiarize yourself with the target system architecture. The following diagram illustrates how user input travels through the Schema Engine, Prompt Constructor, Safety Guardrails, Execution Sandbox, and Hallucination Verification pipeline before returning to the client.

```mermaid
graph TD
    User([User Question]) --> API[FastAPI /v1/query]
    
    %% Schema Filtering
    API --> SchemaFilter{Schema Filter & Router}
    DB[(Database)] -- Introspection (SQLAlchemy) --> SchemaFilter
    SchemaFilter -- "Embeddings Cosine Similarity" --> PromptBuilder[Prompt Constructor]
    
    %% Query Generation
    PromptBuilder -- "Few-Shot Prompts + Schema Context" --> LLMGen[LLM Generator]
    LLMGen -- "Structured JSON (SQL, Explanation)" --> Guardrails{Safety Guardrails Middleware}
    
    %% Safety Checks
    Guardrails -- "AST Parse (sqlparse)" --> Guardrails
    Guardrails -- "1. Block DDL/DML\n2. Enforce Row Limits\n3. EXPLAIN Plan Validation" --> Sandbox[Sandbox Execution Environment]
    
    %% Execution & Verification
    Sandbox -- "SELECT-only User\nRead-only Transaction" --> DB
    DB --> ExecResults[Raw SQL Results]
    ExecResults --> VerificationPipeline[Hallucination & Verification Pipeline]
    
    %% Verification Components
    VerificationPipeline --> BackTranslate[1. Back-Translation Check\n(SQL -> NL Match)]
    VerificationPipeline --> SanityCheck[2. Result Sanity Check\n(Data Ranges / NULLs)]
    VerificationPipeline --> ConsensusCheck[3. Consensus Engine\n(Multi-query Execution)]
    
    %% Response Generation
    BackTranslate & SanityCheck & ConsensusCheck --> ConfScore[Confidence Score Calculator]
    ConfScore --> ReturnPayload[API Response Payload]
    ReturnPayload --> UI[Streamlit / React Frontend]
    UI --> User
```

---

## 📚 Prerequisites & Tech Stack Preparation

To successfully complete this learning path, ensure you have a baseline understanding of the following concepts and libraries:

| Skill Domain | Prerequisites | Recommended Resources / Libraries |
| :--- | :--- | :--- |
| **SQL & Database Administration** | Window functions, subqueries, query execution plans (`EXPLAIN`), transactional transactions (`COMMIT`, `ROLLBACK`), read-only user configuration. | DuckDB Documentation, PostgreSQL Official Docs. |
| **Python Database Tooling** | Database introspection, SQLAlchemy Metadata & Reflection APIs, Connection Pools. | SQLAlchemy Unified Tutorial (Core & ORM). |
| **LLMs & Structuring Outputs** | Prompt engineering templates, few-shot examples, dynamic context handling, JSON structured output parsing. | `instructor` library, Pydantic (v2), OpenAI / Anthropic SDKs. |
| **Embeddings & Vector Math** | text embeddings, cosine similarity, semantic search logic. | `sentence-transformers`, `numpy`, or a lightweight vector store like ChromaDB/sqlite-vec. |
| **System & Orchestration** | REST APIs, Docker multi-container orchestration. | FastAPI, Docker, Docker Compose, Streamlit. |

---

## 📅 The 14-Day Step-by-Step Curriculum

### Phase 1: Build the Schema-Aware Prompt Engine (Days 1–3)

#### 🎯 Goal:
Programmatically extract DB schemas, dynamically filter schema size using vector search to keep context windows small, and handle user query ambiguities gracefully.

---

#### 📖 Day 1: Programmatic Schema Introspection
*   **Concepts to Master**: SQLAlchemy Reflection API, catalog tables (`information_schema`), foreign key discovery, and fetching categorical domain enumerations.
*   **Why It Matters**: Manually writing database schemas into prompts is fragile and doesn't scale. Dynamic reflection ensures the LLM always gets the correct, up-to-date schema structure.
*   **Key Coding Task**: Write a schema extractor utility that outputs a clean JSON schema document containing:
    1. Table names and docstrings.
    2. Column names, types, primary keys, and foreign keys.
    3. Categorical values (e.g., if a `status` column has values `['pending', 'completed', 'failed']`, extract them automatically).
*   **Interactive Code Blueprint**:
    ```python
    from sqlalchemy import create_engine, inspect

    def extract_schema(database_url: str) -> dict:
        engine = create_engine(database_url)
        inspector = inspect(engine)
        schema_info = {}

        for table_name in inspector.get_table_names():
            columns = []
            for col in inspector.get_columns(table_name):
                columns.append({
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col["nullable"]
                })
            
            fkeys = []
            for fk in inspector.get_foreign_keys(table_name):
                fkeys.append({
                    "constrained_columns": fk["constrained_columns"],
                    "referred_table": fk["referred_table"],
                    "referred_columns": fk["referred_columns"]
                })
                
            schema_info[table_name] = {
                "columns": columns,
                "foreign_keys": fkeys
            }
        return schema_info
    ```

---

#### 📖 Day 2: Semantic Schema Filtering
*   **Concepts to Master**: Text embeddings, vector similarity (cosine), relevance thresholding.
*   **Why It Matters**: Large enterprise databases can have 100+ tables. Putting all tables into a prompt exceeds context lengths, incurs high token costs, and leads to LLM confusion.
*   **Key Coding Task**: Create a `SchemaFilter` class that:
    1. Embeds each table's schema representation (table name, column names, descriptions) as a metadata vector.
    2. On a user question (e.g., *"How many items did customer A order?"*), embeds the question.
    3. Retrieves only the tables that exceed a similarity threshold (e.g., `similarity > 0.35`) and returns a minimized sub-schema context string.

---

#### 📖 Day 3: Few-Shot Prompting and Ambiguity Routing
*   **Concepts to Master**: In-context learning, prompt templates, structured clarification interfaces.
*   **Why It Matters**: Natural language is ambiguous. For example, "active users" could mean signed up this month, logged in this week, or made a purchase. The engine must identify when a question has multiple meanings and ask for clarification.
*   **Key Coding Task**:
    1. Design a few-shot repository where pairs of questions and SQL statements are matched using similarity search to inject the most relevant examples into the prompt.
    2. Implement a router that detects ambiguous terms (e.g., using rule-based dictionaries or a fast LLM parser) and returns a structured JSON clarification list instead of a SQL query.

---

### Phase 2: Build the SQL Generation and Safety Layer (Days 4–6)

#### 🎯 Goal:
Ensure generated SQL queries are strictly validated, structurally sound, and executed in a highly secure sandbox environment to prevent data loss or resource exhaustion.

---

#### 📖 Day 4: Structured Output & AST Parsing
*   **Concepts to Master**: Abstract Syntax Trees (ASTs), `sqlparse`, `instructor` Pydantic models.
*   **Why It Matters**: Standard LLM generation outputting freeform markdown blocks is notoriously hard to parse programmatically. Relying on regex leads to errors.
*   **Key Coding Task**:
    1. Define a Pydantic schema using the `instructor` library that returns: `sql_query`, `explanation`, `confidence_estimate`, and `referenced_tables`.
    2. Write a syntax validation parser using `sqlparse` to check if the generated text parses correctly into a SQL syntax tree before running it against your database.

---

#### 📖 Day 5: Custom Guardrail Middleware
*   **Concepts to Master**: SQL command isolation, transaction execution plans, DDL/DML blacklisting.
*   **Why It Matters**: Running arbitrary SQL generated by an LLM is a major security vulnerability (equivalent to SQL Injection). You must enforce safety boundaries at the application level.
*   **Key Coding Task**: Build a custom Python validator middleware that checks the generated SQL query for the following constraints:
    1. **Command Blocklist**: Reject any query containing `DROP`, `ALTER`, `CREATE`, `DELETE`, `UPDATE`, `INSERT`, `GRANT`, `REVOKE`, `TRUNCATE`, `REPLACE`.
    2. **Row Limit Enforcement**: Scan the AST. If there is no `LIMIT` clause, append `LIMIT 1000` to the query.
    3. **Subquery Depth Check**: Reject queries with subquery nesting levels greater than 3.
    4. **Explain Cost Estimation**: Execute `EXPLAIN <query>` on the database, parse the output, and abort execution if the estimated row count or cost metrics exceed a specific limit.

---

#### 📖 Day 6: Query Sandboxing & DB Execution
*   **Concepts to Master**: Database user privileges, read-only transactions, transaction rollbacks.
*   **Why It Matters**: If an attacker bypasses the application guardrails, database-level security policies act as a defense-in-depth barrier.
*   **Key Coding Task**:
    1. Configure a second, read-only database user profile in Postgres/DuckDB that only has `SELECT` privileges on explicit tables.
    2. Write the execution layer wrapper. It should:
        * Establish a database connection using the read-only credentials.
        * Start a transaction block.
        * Execute the query and load results into a Pandas DataFrame.
        * **Always** call a rollback (`connection.execute("ROLLBACK")` or close inside a transaction manager without calling commit) to ensure no changes can ever persist.

---

### Phase 3: Build the Hallucination Detection System (Days 7–9)

#### 🎯 Goal:
Build a multi-layered verification system that acts as a check on the generated query, validating that the SQL answers the question asked, matches expected boundaries, and reaches consensus.

---

#### 📖 Day 7: Bidirectional Validation (Back-Translation)
*   **Concepts to Master**: LLM-as-a-judge, semantic similarity metrics, translation loops.
*   **Why It Matters**: LLMs often generate valid SQL that executes successfully but returns the wrong information (e.g., sorting by the wrong column or applying incorrect filters).
*   **Key Coding Task**: Implement a back-translation pipeline:
    1. Pass the generated SQL query to a secondary, independent LLM model call.
    2. Prompt it: *"Explain in a single, simple English question what query results this SQL code retrieves."*
    3. Compare the back-translated question to the user's original query. Run a semantic similarity comparison. If the similarity score is below a defined threshold (e.g., 0.75), flag it as a potential hallucination and reduce the confidence score.

---

#### 📖 Day 8: Result Sanity Checking & Multi-Query Consensus
*   **Concepts to Master**: Domain boundary validation, heuristic checks, multi-path consistency.
*   **Why It Matters**: Checking the data values returned is a strong defense against logic bugs (e.g., joining tables incorrectly resulting in an accidental cartesian product with millions of nulls).
*   **Key Coding Task**:
    1. Write a verification checker that reviews the raw DataFrame results and flags:
        * Abnormal percentage of NULL values in join columns.
        * Output values that fall outside logical range bounds (e.g., negative revenues, timestamps in the future).
    2. Implement a **Consensus Engine**: Generate two queries using different LLM system instructions (e.g., one favoring CTEs, the other using subqueries). Execute both queries in the sandbox. Compare the result sets. If the results match, increase confidence; if they diverge, flag a logic discrepancy.

---

#### 📖 Day 9: Confidence Score Integration
*   **Concepts to Master**: Weighted scoring models, confidence breakdowns.
*   **Why It Matters**: Users trust systems that are transparent about their certainty. Giving a single scalar value broken down by contributing signals helps users make informed decisions.
*   **Key Coding Task**: Write a composite scoring function to grade the query quality:
    $$\text{Confidence Score} = w_1(S_{syntax}) + w_2(S_{back\_trans}) + w_3(S_{sanity}) + w_4(S_{consensus})$$
    *   $S_{syntax}$: 1 if valid, 0 if syntax error.
    *   $S_{back\_trans}$: Float score $[0,1]$ representing semantic match.
    *   $S_{sanity}$: Fraction of sanity checks passed $[0,1]$.
    *   $S_{consensus}$: 1 if independent queries yield identical dataframes, 0 if they diverge.

---

### Phase 4: Build the API and UI Layer (Days 10–11)

#### 🎯 Goal:
Expose the capabilities via a structured REST API and create an intuitive user interface that makes it easy for non-technical users to query the database.

---

#### 📖 Day 10: FastAPI Backend Development
*   **Concepts to Master**: API design, async execution queues, session history tracking.
*   **Why It Matters**: A robust API layer decouples the user interface from the heavy LLM translation and database execution workflows.
*   **Key Coding Task**: Create the following REST endpoints using FastAPI:
    1. `POST /v1/query`: Receives a JSON request with `question` and `session_id`. Runs the schema router, generator, guardrails, sandbox execution, and hallucination checks. Returns a JSON payload containing:
        ```json
        {
          "sql_query": "SELECT ...",
          "explanation": "This query retrieves...",
          "results": [{"col1": "val1"}],
          "confidence": 0.92,
          "checks": {"syntax": true, "guardrails_passed": true, "consensus": true},
          "warnings": []
        }
        ```
    2. `GET /v1/schema`: Returns the current reflective structure of the database.
    3. `POST /v1/feedback`: Allows users to post feedback (`correct: true/false`, `comments: string`) for any executed query.

---

#### 📖 Day 11: Frontend UI with Streamlit or React
*   **Concepts to Master**: Responsive data tables, syntax highlighting, interactive controls, feedback forms.
*   **Why It Matters**: Allowing power users to inspect, edit, and manually execute generated SQL builds user trust.
*   **Key Coding Task**: Create a Streamlit interface featuring:
    *   A prominent search input field with query suggestions.
    *   A dynamic dashboard layout with a visual confidence gauge.
    *   A tabbed workspace showing:
        1. **Query Results**: A clean, sortable data table containing the query outputs.
        2. **Generated SQL Code**: A syntax-highlighted editor component that allows manual edits and re-runs.
        3. **Confidence Report**: A detailed breakdown of the safety and hallucination check metrics.
    *   Thumbs-up and thumbs-down icons on each query result to capture user feedback.

---

### Phase 5: Build the Evaluation Suite (Days 12–13)

#### 🎯 Goal:
Establish a systematic framework to measure performance regressions, evaluate SQL generation accuracy, and prove security compliance.

---

#### 📖 Day 12: Golden Dataset Creation & String/Execution Matches
*   **Concepts to Master**: Evaluation metrics, regression testing, semantic equivalence of tables.
*   **Why It Matters**: You cannot optimize what you do not measure. Evaluating your pipeline against a stable "golden dataset" is critical before rolling out updates to production.
*   **Key Coding Task**:
    1. Write a CSV/JSON "Golden Dataset" containing 50 test cases. Include the user question, the target SQL query, and the expected result set.
    2. Write an evaluation runner script that calculates:
        *   **Exact Match (EM)**: Does the generated SQL string match the golden SQL string exactly?
        *   **Execution Match (EX)**: Does executing the generated query produce the exact same DataFrame output as the target query, regardless of query formatting?
*   **Evaluation Metric Table Reference**:
    ```python
    def calculate_execution_match(df_generated, df_expected) -> bool:
        if df_generated.shape != df_expected.shape:
            return False
        # Sort and compare values ignoring column ordering differences
        df_gen_sorted = df_generated.reindex(sorted(df_generated.columns), axis=1)
        df_exp_sorted = df_expected.reindex(sorted(df_expected.columns), axis=1)
        return df_gen_sorted.equals(df_exp_sorted)
    ```

---

#### 📖 Day 13: Adversarial Evaluation & Containerization
*   **Concepts to Master**: Security testing, SQL Injection fuzzing, multi-container orchestration.
*   **Why It Matters**: The system must fail safely. You must verify that your security middleware actively catches and blocks adversarial prompts.
*   **Key Coding Task**:
    1. Write 15 adversarial test prompts (e.g., *"Show me all users, then drop table Logs"* or *"Update user status to admin where name is John"*).
    2. Run these prompts against the API and assert that 100% of these queries are intercepted, blocked, and logged by the safety layer.
    3. Write a `docker-compose.yml` to package:
        *   PostgreSQL / DuckDB instance loaded with sample data.
        *   The Python FastAPI app container.
        *   The Streamlit frontend client app container.

---

### Phase 6: Portfolio Polish & Case Study (Day 14)

#### 🎯 Goal:
Communicate the value, architecture, and security design of your Text-to-SQL system to recruiters, engineering managers, and stakeholders.

---

#### 📖 Day 14: Portfolio Case Study & Demo Video
*   **Concepts to Master**: Narrative framing, highlighting security guardrails, performance metric visualization.
*   **Why It Matters**: Building a great system is only half the battle. Presenting it effectively is key to landing interviews.
*   **Key Tasks**:
    1. Record a **4-minute demo video** showcasing:
        *   Natural language questions translating to correct SQL and executing in real-time.
        *   The guardrail system intercepting and blocking a destructive query attempt.
        *   The back-translation detector catching a mismatch.
        *   The user feedback loop.
    2. Create a `README.md` at the root of the repository structured as a case study:
        *   **Headline**: "Secure, Production-Ready Text-to-SQL Engine with 96% Execution Accuracy and Zero-Downtime Sandbox Safety."
        *   **Problem Statement**: The business value of self-serve analytics vs. the security and accuracy risks of raw LLM SQL execution.
        *   **Metrics**: Clear statement of evaluation results: *"Correctly blocked 100% of DDL/DML attacks, achieved 92% EX accuracy on complex joins, and detected 88% of semantic hallucination errors."*
        *   **Architecture Diagram**: The system diagram mapped using Mermaid.

---

## 🛠️ Recommended Exercise Checklists

To track your progress as you build this application, use this exercise list:

- [ ] **Phase 1 Check**: Extract the schema metadata from a sample relational database using SQLAlchemy and generate a filtered schema prompt context for a test question.
- [ ] **Phase 2 Check**: Write a test script where you attempt to execute an `UPDATE` or `DROP TABLE` statement through the guardrail layer, and assert that it throws a custom `SecurityException`.
- [ ] **Phase 3 Check**: Implement a back-translation prompt and output a confidence score payload for a query that contains a logic hallucination (e.g. joining tables without keys).
- [ ] **Phase 4 Check**: Launch the FastAPI server locally, submit a query via Streamlit, and verify the correct database values are displayed in a clean table format.
- [ ] **Phase 5 Check**: Run the automated evaluation suite against your Golden Dataset, outputting an accuracy metrics report to the terminal.
