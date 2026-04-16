from langchain_core.messages import AIMessage

from agent.nodes.base import BaseNode
from agent.state import AgentState

# Teams truncates messages above this character count
TEAMS_MESSAGE_CHAR_LIMIT = 28_000


class ResponseBuilderNode(BaseNode):
    async def _run(self, state: AgentState) -> dict:
        rows = state.get("query_result") or []
        content = _build_content(rows)
        return {"messages": [AIMessage(content=content)]}


def _build_content(rows: list[dict]) -> str:
    if not rows:
        return "No results found for your query."
    table = _format_as_markdown_table(rows)
    if len(table) > TEAMS_MESSAGE_CHAR_LIMIT:
        # Truncate and inform — never silently drop data
        return table[:TEAMS_MESSAGE_CHAR_LIMIT] + "\n\n_Results truncated. Narrow your query._"
    return table


def _format_as_markdown_table(rows: list[dict]) -> str:
    if not rows:
        return ""
    headers = list(rows[0].keys())
    header_row = "| " + " | ".join(headers) + " |"
    separator  = "| " + " | ".join("---" for _ in headers) + " |"
    data_rows  = [
        "| " + " | ".join(str(row.get(h, "")) for h in headers) + " |"
        for row in rows
    ]
    return "\n".join([header_row, separator] + data_rows)
