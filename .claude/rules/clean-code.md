## Clean Code Rules

### Functions do one thing
A function is too big if you can describe what it does with the word "and".
Target: ≤ 20 lines of logic per function. If it grows beyond that, extract.

```python
# Bad — does three things
async def process_message(state):
    sql = await llm.invoke(build_prompt(state["messages"]))
    is_safe, reason = validate_sql(sql.content)
    if not is_safe:
        return {"error": reason}
    rows = await engine.execute(sql.content)
    return {"query_result": rows}

# Good — each concern is named and isolated
async def nl2sql_node(state, llm, schema):
    sql = await _generate_sql(state["messages"], schema, llm)
    return {"generated_sql": sql}

async def guardrail_node(state):
    is_safe, reason = validate_sql(state["generated_sql"])
    return {"sql_is_safe": is_safe, "error": None if is_safe else reason}

async def executor_node(state, engine):
    rows = await _run_query(state["generated_sql"], engine)
    return {"query_result": rows}
```

### Meaningful names — no abbreviations, no generic terms
Names should reveal intent. Avoid: `data`, `result`, `obj`, `tmp`, `res`, `val`, `mgr`.

```python
# Bad
def proc(q, s):
    res = s.get(q)
    return res

# Good
def get_schema_context(question: str, registry: SchemaRegistry) -> str:
    return registry.get_tables_for_question(question)
```

### No magic strings or numbers
Every literal that carries meaning belongs in a named constant.

```python
# Bad
if llm_provider == "azure_openai":
    ...
if len(rows) > 500:
    ...

# Good
PROVIDER_AZURE_OPENAI = "azure_openai"
MAX_QUERY_ROWS = 500

if llm_provider == PROVIDER_AZURE_OPENAI:
    ...
if len(rows) > MAX_QUERY_ROWS:
    ...
```

### Comments explain WHY, not WHAT
The code says what. Comments say why — the decision, the constraint, the non-obvious context.

```python
# Bad
# loop through rows
for row in rows:
    ...

# Good
# SQL Server returns Decimal for BRL columns — convert to float
# so the JSON serializer doesn't blow up when building the Teams card
for row in rows:
    row["valor_brl"] = float(row["valor_brl"])
```

### Prefer early return over nested conditionals
```python
# Bad
async def executor_node(state, engine):
    if state["sql_is_safe"]:
        if state["generated_sql"]:
            rows = await _run_query(state["generated_sql"], engine)
            if rows:
                return {"query_result": rows}
    return {"query_result": None}

# Good
async def executor_node(state, engine):
    if not state["sql_is_safe"]:
        return {"query_result": None}
    if not state["generated_sql"]:
        return {"query_result": None}
    rows = await _run_query(state["generated_sql"], engine)
    return {"query_result": rows or []}
```

### No dead code
Delete commented-out code. Use git history if you need it back.
Never leave `# TODO` without a linked issue. Resolve or delete before merging.

### Don't repeat yourself — but don't abstract prematurely
Extract shared logic only when the same concept appears in three or more places.
Two similar lines are fine. Three identical blocks → extract a function.

### Fail loudly at boundaries, silently nowhere else
Validate at entry points (Teams message handler, config load). Inside the agent pipeline, propagate errors through `state["error"]` — never swallow exceptions silently.

```python
# Bad — silent failure masks bugs
async def executor_node(state, engine):
    try:
        rows = await _run_query(state["generated_sql"], engine)
        return {"query_result": rows}
    except Exception:
        return {"query_result": None}  # hides the real error

# Good — surface the error through state
async def executor_node(state, engine):
    try:
        rows = await _run_query(state["generated_sql"], engine)
        return {"query_result": rows, "error": None}
    except SQLAlchemyError as exc:
        return {"query_result": None, "error": f"DB error: {exc}"}
```

### Module cohesion
Keep related things together. `agent/nodes/nl2sql.py` owns everything about SQL generation.
`db/executor.py` owns everything about query execution. Don't let DB logic leak into nodes or vice versa.
