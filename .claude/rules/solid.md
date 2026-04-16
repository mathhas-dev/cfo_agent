## SOLID Principles

### S — Single Responsibility
Each module, class, and function has exactly one reason to change.

**Apply it:**
- `validate_sql()` only validates — does not log, does not raise HTTP errors
- `SchemaRegistry` only loads and queries schema metadata — does not format prompts
- Each LangGraph node writes to one concern: nl2sql writes SQL, guardrail writes safety flag, executor writes results
- Bot Framework adapter translates Teams ↔ agent messages — it does not contain business logic

**Red flag:** a function whose name contains "and" (`validate_and_execute`, `build_and_send`).
Split it.

---

### O — Open/Closed
Open for extension, closed for modification.

**Apply it:**
- LLM providers are added by implementing `BaseChatModel` and registering in the factory — not by editing existing provider code
- Schema Registry supports new table entries without touching the query logic
- New LangGraph nodes are added by plugging into the graph — existing nodes are not modified
- SQL blocking rules are defined as a data structure (list of patterns), not hardcoded `if` branches

```python
# Closed for modification — extend by adding to BLOCKED_PATTERNS
BLOCKED_PATTERNS: list[re.Pattern] = [
    re.compile(r'\bDELETE\b', re.IGNORECASE),
    re.compile(r'\bDROP\b',   re.IGNORECASE),
    # add new patterns here without touching validate_sql()
]

def validate_sql(sql: str) -> tuple[bool, str]:
    for pattern in BLOCKED_PATTERNS:
        if pattern.search(sql):
            return False, f"Blocked pattern: {pattern.pattern}"
    return True, ""
```

---

### L — Liskov Substitution
Any concrete LLM implementation must be fully substitutable for `BaseChatModel` without breaking the agent.

**Apply it:**
- `nl2sql_node` accepts `BaseChatModel` — it never checks `isinstance(llm, ChatOllama)`
- `SqlExecutor` accepts `Engine` from SQLAlchemy — callers never depend on the concrete driver (pyodbc vs. aioodbc)
- LangGraph checkpointers (`MemorySaver`, `SqliteSaver`) are swapped without node changes

**Test it:** every node unit test must pass with both a real LLM and a `FakeChatModel` stub that satisfies the `BaseChatModel` interface.

---

### I — Interface Segregation
Don't force a class to depend on methods it doesn't use.

**Apply it:**
- `nl2sql_node` reads only `state["messages"]` and `state["schema_context"]` — it must not receive the full `AgentState` dict unpacked as kwargs
- Schema Registry exposes two methods: `get_full_schema() -> str` and `get_tables_for_question(question: str) -> str`. The nl2sql node only needs one at a time.
- Bot adapter exposes `receive(activity) -> str` and `send(conversation_id, text)` — LangGraph agent does not import `botbuilder` types

```python
# Narrow protocol — node only depends on what it actually uses
from typing import Protocol

class SchemaProvider(Protocol):
    def get_schema_context(self, question: str) -> str: ...

# nl2sql_node depends on SchemaProvider, not on SchemaRegistry directly
async def nl2sql_node(state: AgentState, schema: SchemaProvider, llm: BaseChatModel) -> dict:
    ...
```

---

### D — Dependency Inversion
High-level modules depend on abstractions, not concretions.

**Apply it:**
- `agent/graph.py` (high-level) depends on node functions with typed signatures — not on Ollama or SQLAlchemy directly
- `nl2sql_node` receives `llm: BaseChatModel` injected at graph build time — it does not instantiate the LLM itself
- `SqlExecutor` receives `engine: Engine` — it does not call `create_engine()` internally
- `SchemaRegistry` is injected into nodes as a `SchemaProvider` protocol — not imported directly

```python
# graph.py — wires dependencies at the top, injects into nodes
from config import settings
from db.engine import build_engine
from schema_registry.registry import SchemaRegistry
from agent.llm_factory import get_llm

llm = get_llm()
engine = build_engine(settings.db_connection_string.get_secret_value())
schema = SchemaRegistry.from_file("schema_registry/schema.yaml")

# nodes receive their dependencies — graph owns the wiring
graph.add_node("nl2sql", partial(nl2sql_node, llm=llm, schema=schema))
graph.add_node("executor", partial(executor_node, engine=engine))
```
