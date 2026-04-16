from langchain_core.messages import AIMessage

from agent.nodes.base import BaseNode
from agent.state import AgentState

# Generic message — internal error details are never surfaced to the user
# (sql-safety.md: "never expose raw SQL or guardrail rejection reason")
GENERIC_ERROR_MESSAGE = (
    "I was unable to process your request. "
    "Please rephrase your question and try again."
)


class ErrorHandlerNode(BaseNode):
    async def _run(self, state: AgentState) -> dict:
        return {"messages": [AIMessage(content=GENERIC_ERROR_MESSAGE)]}
