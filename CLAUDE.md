## Project
CFOAgent — NL2SQL financial BI agent. Directors query P&L data in natural language via Microsoft Teams.
Pattern: `user message → LangGraph agent → NL→SQL → guardrail → SQL Server → formatted table`.

**Not RAG.** Retrieval = schema context injection, not document chunks.

## Stack
- Python 3.11+, uv (package manager)
- `langchain` + `langchain-community` — orchestration
- `langgraph` — stateful agent + session memory
- `sqlalchemy` + `pyodbc` — SQL Server
- `botbuilder-core` — Teams Bot Framework SDK (outside LangChain)
- `pydantic-settings` — env/config management
- `pytest` — tests
- Docker + Azure Container Apps + GitHub Actions — CI/CD
- Dev LLM: `qwen2.5-coder:14b` via Ollama (`ChatOllama`)
- Prod LLM: Azure OpenAI or Anthropic API (env-switched, never hardcoded)

## Architecture
```
Teams → Bot Framework SDK → LangGraph Agent
                                 ├── Schema Registry  ← most critical component
                                 ├── NL→SQL node      ← LLM call
                                 ├── Guardrail node   ← SQL validation (always runs)
                                 ├── Executor node    ← DB query
                                 └── Response Builder ← table formatting for Teams
```
LangGraph State persists conversation history for chained queries across turns.

## Non-negotiable rules

**SQL security:** LLM-generated SQL must always pass through the Guardrail before execution.
Blocked statements: `DELETE`, `UPDATE`, `INSERT`, `DROP`, `CREATE`, `ALTER`, `TRUNCATE`, `EXEC`, `EXECUTE`, `xp_*`, `sp_*`.
See @.claude/rules/sql-safety.md.

**Schema Registry first:** every NL→SQL prompt must include the full schema context. Schema quality determines SQL quality — this is the highest-leverage component.

**No narrative responses:** return data tables only. No LLM-generated interpretation or summaries. Directors want the number, not the analysis.

**LLM config via env:** never hardcode model names, endpoints, or API keys. Switch dev↔prod via `LLM_PROVIDER` env var. See @.claude/rules/config-patterns.md.

## Code conventions
- Snake_case for all Python identifiers
- Type hints on all public functions and methods
- Async/await for all I/O-bound operations (DB, LLM, HTTP)
- Prompts live in `prompts/` as `.txt` or `.jinja2` — never inline strings in code
- Config via `pydantic-settings` `BaseSettings` subclass — never `os.environ` directly
- English for all code, comments, docstrings, commit messages

## Project layout (target)
```
cfo_agent/
├── agent/          # LangGraph graph, nodes, state definition
├── db/             # SQLAlchemy engine, executor
├── prompts/        # .jinja2 prompt templates
├── schema_registry/# table/column metadata for schema injection
├── teams/          # Bot Framework adapter
├── config.py       # pydantic-settings BaseSettings
└── tests/
```

## Rules
@.claude/rules/sql-safety.md
@.claude/rules/langgraph-patterns.md
@.claude/rules/testing.md
@.claude/rules/config-patterns.md
@.claude/rules/solid.md
@.claude/rules/clean-code.md
@.claude/rules/design-patterns.md
