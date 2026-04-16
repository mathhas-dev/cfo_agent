from pathlib import Path

import pytest

from schema_registry.registry import SchemaRegistry

_SCHEMA_PATH = Path(__file__).parent.parent.parent / "schema_registry" / "schema.yaml"


@pytest.fixture(scope="module")
def registry() -> SchemaRegistry:
    return SchemaRegistry.from_file(_SCHEMA_PATH)


def test_loads_without_error(registry: SchemaRegistry) -> None:
    assert registry is not None


def test_all_entries_are_valid(registry: SchemaRegistry) -> None:
    errors = registry.validate()
    assert errors == [], f"Schema registry validation errors:\n" + "\n".join(errors)


def test_full_schema_contains_fact_pnl(registry: SchemaRegistry) -> None:
    assert "fact_pnl" in registry.get_full_schema()


def test_full_schema_contains_all_three_tables(registry: SchemaRegistry) -> None:
    schema = registry.get_full_schema()
    assert "fact_pnl" in schema
    assert "dim_centro_custo" in schema
    assert "dim_tempo" in schema


def test_full_schema_includes_column_descriptions(registry: SchemaRegistry) -> None:
    schema = registry.get_full_schema()
    # Spot-check a business-critical column description
    assert "EBITDA" in schema


def test_schema_for_question_returns_non_empty_string(registry: SchemaRegistry) -> None:
    context = registry.get_schema_for_question("qual foi o EBITDA em janeiro?")
    assert isinstance(context, str)
    assert len(context) > 0


def test_schema_format_is_sql_like(registry: SchemaRegistry) -> None:
    schema = registry.get_full_schema()
    assert "CREATE TABLE" in schema
    assert "DECIMAL" in schema


def test_every_column_has_description() -> None:
    """A column without a description is a production bug — it degrades SQL quality."""
    registry = SchemaRegistry.from_file(_SCHEMA_PATH)
    errors = registry.validate()
    description_errors = [e for e in errors if "missing a description" in e]
    assert description_errors == [], f"Columns missing descriptions: {description_errors}"
