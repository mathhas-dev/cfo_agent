"""Integration tests — require a running Ollama instance.

Run with: pytest -m ollama
Skip automatically in CI if Ollama is not available.

No LLM mocking here (testing.md: mocking the LLM hides prompt regression).
"""
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest
from langchain_core.messages import HumanMessage

from agent.nodes.guardrail import validate_sql
from schema_registry.registry import SchemaRegistry

_SCHEMA_PATH = Path(__file__).parent.parent.parent / "schema_registry" / "schema.yaml"


def _ollama_is_running() -> bool:
    try:
        urlopen("http://localhost:11434", timeout=2)
        return True
    except (URLError, OSError):
        return False


_OLLAMA_AVAILABLE = _ollama_is_running()


@pytest.fixture(scope="module")
def schema() -> SchemaRegistry:
    return SchemaRegistry.from_file(_SCHEMA_PATH)


@pytest.mark.ollama
@pytest.mark.slow
@pytest.mark.skipif(not _OLLAMA_AVAILABLE, reason="Ollama not running on localhost:11434")
@pytest.mark.parametrize(
    "question",
    [
        "qual foi o EBITDA total em janeiro de 2024?",
        "quais são as receitas brutas por região no Q1 2024?",
        "compare o lucro líquido de 2023 e 2024",
    ],
)
async def test_nl2sql_generates_safe_select(question: str, schema: SchemaRegistry) -> None:
    from agent.llm_factory import _build_ollama
    from agent.nodes.nl2sql import NL2SqlNode

    node = NL2SqlNode(llm=_build_ollama(), schema=schema)
    state = {
        "messages": [HumanMessage(content=question)],
        "schema_context": None,
        "generated_sql": None,
        "sql_is_safe": None,
        "query_result": None,
        "error": None,
    }

    result = await node(state)

    assert result.get("error") is None, f"Node returned error: {result.get('error')}"

    sql = result.get("generated_sql", "")
    assert sql, "Node returned empty SQL"
    assert sql.strip().upper().startswith("SELECT"), f"Expected SELECT, got: {sql[:80]}"

    is_safe, reason = validate_sql(sql)
    assert is_safe, f"LLM generated unsafe SQL ({reason}): {sql}"
