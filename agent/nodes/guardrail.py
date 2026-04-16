"""SQL guardrail — Chain of Responsibility pattern.

Each handler checks one specific concern.
To add a new validation rule, add a new handler class and wire it in
_build_chain() — existing handlers are not modified (Open/Closed Principle).
"""
import re
from abc import ABC, abstractmethod

# Strip comments before validation to prevent obfuscation attacks
_LINE_COMMENT = re.compile(r"--[^\n]*")
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)

# DML mutations and DDL statements (sql-safety.md)
_BLOCKED_KEYWORDS = re.compile(
    r"\b(DELETE|UPDATE|INSERT|MERGE|DROP|CREATE|ALTER|TRUNCATE|RENAME"
    r"|EXEC|EXECUTE|OPENROWSET|OPENQUERY|sp_executesql)\b",
    re.IGNORECASE,
)

# Extended stored procedures (xp_) and system procs (sp_) by prefix
_PROC_PREFIX = re.compile(r"\b(xp_|sp_)\w+", re.IGNORECASE)


def _strip_comments(sql: str) -> str:
    without_line = _LINE_COMMENT.sub("", sql)
    return _BLOCK_COMMENT.sub("", without_line)


class SqlValidationHandler(ABC):
    def __init__(self) -> None:
        self._next: "SqlValidationHandler | None" = None

    def set_next(self, handler: "SqlValidationHandler") -> "SqlValidationHandler":
        self._next = handler
        return handler

    @abstractmethod
    def handle(self, sql: str) -> tuple[bool, str]:
        ...

    def _pass_to_next(self, sql: str) -> tuple[bool, str]:
        if self._next:
            return self._next.handle(sql)
        return True, ""


class BlockedKeywordHandler(SqlValidationHandler):
    """Rejects SQL containing DML/DDL mutation keywords."""

    def handle(self, sql: str) -> tuple[bool, str]:
        if _BLOCKED_KEYWORDS.search(sql):
            return False, "Query contains a disallowed statement"
        return self._pass_to_next(sql)


class StackedQueryHandler(SqlValidationHandler):
    """Rejects SQL with multiple statements separated by semicolons."""

    def handle(self, sql: str) -> tuple[bool, str]:
        # A lone trailing semicolon is harmless — strip it before checking
        if ";" in sql.rstrip().rstrip(";"):
            return False, "Stacked queries are not allowed"
        return self._pass_to_next(sql)


class ExtendedProcHandler(SqlValidationHandler):
    """Rejects calls to extended (xp_) and system (sp_) stored procedures."""

    def handle(self, sql: str) -> tuple[bool, str]:
        if _PROC_PREFIX.search(sql):
            return False, "Stored procedure calls are not allowed"
        return self._pass_to_next(sql)


def _build_chain() -> SqlValidationHandler:
    head = BlockedKeywordHandler()
    head.set_next(StackedQueryHandler()).set_next(ExtendedProcHandler())
    return head


# Module-level chain — stateless handlers, safe to reuse across calls
_CHAIN: SqlValidationHandler = _build_chain()


def validate_sql(sql: str) -> tuple[bool, str]:
    """Entry point. Strips comments then runs through the validation chain.

    Returns (is_safe, reason). Always call before executing LLM-generated SQL.
    """
    clean = _strip_comments(sql)
    return _CHAIN.handle(clean)


# --- LangGraph node wrapper ---
# Imported here to avoid a separate file for a thin adapter.
# Cohesion: all guardrail concerns live in this module.

from agent.nodes.base import BaseNode  # noqa: E402
from agent.state import AgentState  # noqa: E402


class GuardrailNode(BaseNode):
    """Runs validate_sql and writes sql_is_safe to state.

    On failure the error is set to a generic message — the real reason is
    captured by the AuditCallbackHandler and never exposed to the user
    (sql-safety.md).
    """

    def _check_preconditions(self, state: AgentState) -> str | None:
        if not state.get("generated_sql"):
            return "No SQL to validate"
        return None

    async def _run(self, state: AgentState) -> dict:
        is_safe, _internal_reason = validate_sql(state["generated_sql"])
        if is_safe:
            return {"sql_is_safe": True, "error": None}
        return {"sql_is_safe": False, "error": "Query could not be processed"}
