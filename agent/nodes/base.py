"""Template Method pattern — defines the execution structure for all LangGraph nodes.

Subclasses implement _run() and optionally override _check_preconditions().
Error handling and state propagation are handled here — not in each node.
"""
from abc import ABC, abstractmethod

from agent.state import AgentState


class BaseNode(ABC):
    async def __call__(self, state: AgentState) -> dict:
        if error := self._check_preconditions(state):
            return {"error": error}
        try:
            return await self._run(state)
        except Exception as exc:
            return {"error": str(exc)}

    def _check_preconditions(self, state: AgentState) -> str | None:
        """Return an error message string if preconditions fail, else None."""
        return None

    @abstractmethod
    async def _run(self, state: AgentState) -> dict:
        ...
