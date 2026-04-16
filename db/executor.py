"""Facade pattern — hides all SQLAlchemy complexity behind execute().

Nodes call execute() and receive a list of plain dicts. They never touch
Engine, Connection, or Row objects directly (Facade + Dependency Inversion).
"""
import asyncio
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.engine import Engine

MAX_QUERY_ROWS = 500


class SqlExecutor:
    """Facade over SQLAlchemy. The only public method nodes need is execute()."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    async def execute(self, sql: str) -> list[dict]:
        # pyodbc doesn't support native async — run the sync query in a thread
        # pool so the event loop isn't blocked during DB round-trips
        return await asyncio.to_thread(self._execute_sync, sql)

    def _execute_sync(self, sql: str) -> list[dict]:
        with self._engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = [dict(row._mapping) for row in result]
            return [self._serialize_row(row) for row in rows[:MAX_QUERY_ROWS]]

    def _serialize_row(self, row: dict) -> dict:
        return {key: self._coerce_value(value) for key, value in row.items()}

    def _coerce_value(self, value: object) -> object:
        # SQL Server returns Decimal for DECIMAL/MONEY columns — convert to float
        # so the JSON serializer doesn't blow up when building the Teams message
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        return value
