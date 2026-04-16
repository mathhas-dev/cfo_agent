from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class ColumnEntry:
    name: str
    type: str
    description: str


@dataclass(frozen=True)
class TableEntry:
    name: str
    description: str
    columns: tuple[ColumnEntry, ...]


class SchemaRegistry:
    """Loads and queries P&L schema metadata.

    Single responsibility: schema storage and formatting.
    Does not format LLM prompts — returns plain text context.
    """

    def __init__(self, tables: list[TableEntry]) -> None:
        self._tables = tables

    @classmethod
    def from_file(cls, path: str | Path) -> "SchemaRegistry":
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        tables = [cls._parse_table(entry) for entry in raw["tables"]]
        return cls(tables)

    def get_full_schema(self) -> str:
        return "\n\n".join(self._format_table(t) for t in self._tables)

    def get_schema_for_question(self, question: str) -> str:
        # Returns full schema for now.
        # Future: filter by keyword match to reduce prompt token count.
        return self.get_full_schema()

    def validate(self) -> list[str]:
        """Returns validation errors. Empty list means the registry is valid.

        Called by tests to catch missing descriptions before they cause bad SQL.
        """
        errors: list[str] = []
        for table in self._tables:
            if not table.name:
                errors.append("Table entry is missing a name")
            if not table.description:
                errors.append(f"Table {table.name!r} is missing a description")
            for col in table.columns:
                if not col.description:
                    errors.append(f"{table.name}.{col.name} is missing a description")
                if not col.type:
                    errors.append(f"{table.name}.{col.name} is missing a type")
        return errors

    @staticmethod
    def _parse_table(raw: dict) -> TableEntry:
        columns = tuple(
            ColumnEntry(name=c["name"], type=c["type"], description=c["description"])
            for c in raw["columns"]
        )
        return TableEntry(name=raw["name"], description=raw["description"], columns=columns)

    @staticmethod
    def _format_table(table: TableEntry) -> str:
        header = f"-- {table.name}: {table.description}"
        col_lines = "\n".join(
            f"    {col.name} {col.type}  -- {col.description}"
            for col in table.columns
        )
        return f"{header}\nCREATE TABLE {table.name} (\n{col_lines}\n);"
