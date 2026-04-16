from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage


@pytest.fixture
def fake_llm() -> BaseChatModel:
    """BaseChatModel stub for unit tests.

    Satisfies Liskov Substitution: every node test must pass with a real or
    fake LLM without changing the node code (solid.md — L principle).
    """
    llm = MagicMock(spec=BaseChatModel)
    llm.ainvoke = AsyncMock(
        return_value=AIMessage(
            content="SELECT mes_ref, ebitda_brl FROM fact_pnl WHERE mes_ref = '2024-01'"
        )
    )
    # with_config returns the same stub so the audit callback chain doesn't break
    llm.with_config = MagicMock(return_value=llm)
    return llm


@pytest.fixture
def base_state() -> dict:
    return {
        "messages": [HumanMessage(content="qual foi o EBITDA em janeiro de 2024?")],
        "schema_context": None,
        "generated_sql": None,
        "sql_is_safe": None,
        "query_result": None,
        "error": None,
    }
