import pytest
from langchain_core.messages import HumanMessage

from agent.nodes.response_builder import (
    TEAMS_MESSAGE_CHAR_LIMIT,
    ResponseBuilderNode,
    _format_as_markdown_table,
)


@pytest.fixture
def node() -> ResponseBuilderNode:
    return ResponseBuilderNode()


@pytest.fixture
def state_with_results() -> dict:
    return {
        "messages": [HumanMessage(content="qual o ebitda?")],
        "schema_context": None,
        "generated_sql": "SELECT mes_ref, ebitda_brl FROM fact_pnl",
        "sql_is_safe": True,
        "query_result": [
            {"mes_ref": "2024-01", "ebitda_brl": 1_000_000.0},
            {"mes_ref": "2024-02", "ebitda_brl": 1_100_000.0},
        ],
        "error": None,
    }


@pytest.fixture
def state_empty_results() -> dict:
    return {
        "messages": [HumanMessage(content="qual o ebitda?")],
        "schema_context": None,
        "generated_sql": "SELECT mes_ref, ebitda_brl FROM fact_pnl",
        "sql_is_safe": True,
        "query_result": [],
        "error": None,
    }


async def test_returns_no_results_message_when_query_is_empty(
    node: ResponseBuilderNode, state_empty_results: dict
) -> None:
    result = await node(state_empty_results)
    content = result["messages"][0].content
    assert "No results" in content


async def test_formats_rows_as_markdown_table(
    node: ResponseBuilderNode, state_with_results: dict
) -> None:
    result = await node(state_with_results)
    content = result["messages"][0].content
    assert "mes_ref" in content
    assert "ebitda_brl" in content
    assert "2024-01" in content
    assert "2024-02" in content


async def test_result_is_ai_message(
    node: ResponseBuilderNode, state_with_results: dict
) -> None:
    from langchain_core.messages import AIMessage

    result = await node(state_with_results)
    assert isinstance(result["messages"][0], AIMessage)


async def test_truncates_large_results(node: ResponseBuilderNode) -> None:
    large_state = {
        "messages": [HumanMessage(content="test")],
        "schema_context": None,
        "generated_sql": None,
        "sql_is_safe": True,
        # Generate a table large enough to exceed the Teams limit
        "query_result": [{"col": "x" * 1000} for _ in range(50)],
        "error": None,
    }
    result = await node(large_state)
    content = result["messages"][0].content
    assert len(content) <= TEAMS_MESSAGE_CHAR_LIMIT + 200  # small buffer for truncation suffix
    assert "truncated" in content.lower()


# --- Unit tests for the formatting helper ---


def test_format_empty_list_returns_empty_string() -> None:
    assert _format_as_markdown_table([]) == ""


def test_format_single_row_has_three_lines() -> None:
    rows = [{"mes_ref": "2024-01", "ebitda_brl": 1_000_000.0}]
    lines = _format_as_markdown_table(rows).strip().split("\n")
    assert len(lines) == 3  # header + separator + 1 data row


def test_format_includes_all_column_headers() -> None:
    rows = [{"col_a": "v1", "col_b": 42}]
    table = _format_as_markdown_table(rows)
    assert "col_a" in table
    assert "col_b" in table


def test_format_separator_line_contains_dashes() -> None:
    rows = [{"col_a": "v1"}]
    lines = _format_as_markdown_table(rows).strip().split("\n")
    assert "---" in lines[1]
