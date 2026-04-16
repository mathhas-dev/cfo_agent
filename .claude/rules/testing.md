## Testing Rules

### Test pyramid for this project
- **Unit tests** — guardrail logic, schema registry loading, SQL formatter, response builder
- **Integration tests** — NL→SQL node with real Ollama (dev only, skip in CI without Ollama)
- **No mocking the DB for guardrail tests** — test the actual regex against real SQL strings

### Pytest conventions
```
tests/
├── unit/
│   ├── test_guardrail.py
│   ├── test_schema_registry.py
│   └── test_response_builder.py
├── integration/
│   └── test_nl2sql_node.py   # requires Ollama running, marked @pytest.mark.ollama
└── conftest.py
```

### Guardrail tests are non-negotiable
Any change to `validate_sql` requires tests covering:
- All blocked statement types (DELETE, UPDATE, INSERT, DROP, etc.)
- Obfuscation attempts: mixed case, inline comments, unicode substitution
- Legitimate SELECT queries that must pass
- Stacked queries with semicolons

```python
@pytest.mark.parametrize("sql,expected_safe", [
    ("SELECT * FROM fact_pnl", True),
    ("SELECT 1; DROP TABLE fact_pnl", False),
    ("/* comment */ DELETE FROM fact_pnl", False),
    ("select * from fact_pnl where mes_ref = '2024-01'", True),
])
def test_guardrail(sql, expected_safe):
    is_safe, _ = validate_sql(sql)
    assert is_safe == expected_safe
```

### Markers
```ini
# pyproject.toml [tool.pytest.ini_options]
markers = [
    "ollama: requires local Ollama server",
    "slow: takes more than 5 seconds",
]
```

Run unit tests only: `pytest -m "not ollama and not slow"`

### No LLM mocking in integration tests
Integration tests call the real Ollama endpoint. If Ollama is down, the test is skipped (`pytest.importorskip` pattern), not faked. Mocking the LLM hides prompt regression.

### Schema Registry tests
Test that every column entry in the registry has: table name, column name, non-empty description, and correct data type. A bad registry entry is a production bug.
