import re
from pathlib import Path

import jinja2
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from agent.nodes.base import BaseNode
from agent.state import AgentState
from schema_registry.protocols import SchemaProvider

_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "prompts" / "nl2sql.jinja2"

# Strip markdown code fences the LLM may wrap around the SQL output
_CODE_FENCE = re.compile(r"```(?:sql)?\s*\n?(.*?)\n?```", re.DOTALL | re.IGNORECASE)


def _load_template() -> jinja2.Template:
    return jinja2.Template(_TEMPLATE_PATH.read_text(encoding="utf-8"))


def _extract_sql(raw_response: str) -> str:
    """Remove markdown code fences if present; otherwise return as-is."""
    match = _CODE_FENCE.search(raw_response)
    return match.group(1).strip() if match else raw_response.strip()


def _get_last_user_question(state: AgentState) -> str:
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            return str(message.content)
    return ""


class NL2SqlNode(BaseNode):
    def __init__(self, llm: BaseChatModel, schema: SchemaProvider) -> None:
        self._llm = llm
        self._schema = schema
        self._template = _load_template()

    def _check_preconditions(self, state: AgentState) -> str | None:
        if not state.get("messages"):
            return "No messages in state"
        return None

    async def _run(self, state: AgentState) -> dict:
        question = _get_last_user_question(state)
        schema_context = self._schema.get_schema_for_question(question)
        prompt = self._template.render(schema_context=schema_context, question=question)
        response = await self._llm.ainvoke([HumanMessage(content=prompt)])
        sql = _extract_sql(str(response.content))
        return {"generated_sql": sql, "schema_context": schema_context, "error": None}
