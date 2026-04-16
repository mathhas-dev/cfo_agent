from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    # Conversation history — add_messages reducer appends, never overwrites
    messages: Annotated[list, add_messages]
    # Written by nl2sql node
    schema_context: str | None
    generated_sql: str | None
    # Written by guardrail node
    sql_is_safe: bool | None
    # Written by executor node
    query_result: list[dict] | None
    # Written by any node on failure; cleared on success
    error: str | None
