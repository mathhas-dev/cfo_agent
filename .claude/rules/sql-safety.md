## SQL Safety Rules

### Guardrail is mandatory
Every SQL string produced by the LLM **must** pass through the Guardrail node before reaching the executor. There are no exceptions — not in tests, not in dev mode, not for "simple" queries.

### Blocked statement types
Reject any SQL that contains (case-insensitive, after stripping comments):
- DML mutations: `DELETE`, `UPDATE`, `INSERT`, `MERGE`
- DDL: `DROP`, `CREATE`, `ALTER`, `TRUNCATE`, `RENAME`
- Stored procedure execution: `EXEC`, `EXECUTE`
- Extended procs: `xp_`, `sp_` prefixes
- Dynamic SQL: `sp_executesql`, `OPENROWSET`, `OPENQUERY`, `BULK INSERT`
- Stacked queries: multiple statements separated by `;`

### Guardrail implementation pattern
```python
import re

BLOCKED_PATTERN = re.compile(
    r'\b(DELETE|UPDATE|INSERT|MERGE|DROP|CREATE|ALTER|TRUNCATE|RENAME'
    r'|EXEC|EXECUTE|OPENROWSET|OPENQUERY|BULK\s+INSERT|sp_executesql)\b'
    r'|;\s*\w',
    re.IGNORECASE
)

def validate_sql(sql: str) -> tuple[bool, str]:
    """Returns (is_safe, reason). Always call before executing LLM-generated SQL."""
    clean = re.sub(r'--[^\n]*', '', sql)           # strip line comments
    clean = re.sub(r'/\*.*?\*/', '', clean, flags=re.DOTALL)  # strip block comments
    if BLOCKED_PATTERN.search(clean):
        return False, "Query contains disallowed statement"
    return True, ""
```

### Schema Registry — prompt injection defense
- Strip user input of SQL metacharacters before injecting into the LLM prompt
- Schema Registry entries are static, versioned, and code-reviewed — never built from user input
- Log every LLM-generated SQL before and after guardrail evaluation (for audit trail)

### Read-only DB connection
The SQL Server connection used by the executor must connect with a read-only service account. Defense in depth: guardrail + read-only credentials.

### Never expose raw SQL to the user
Return only the query result table. If the guardrail blocks a query, return a generic error message — never the raw SQL or the guardrail rejection reason.
