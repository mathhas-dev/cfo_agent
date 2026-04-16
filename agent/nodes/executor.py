from agent.nodes.base import BaseNode
from agent.state import AgentState
from db.executor import SqlExecutor


class ExecutorNode(BaseNode):
    def __init__(self, executor: SqlExecutor) -> None:
        self._executor = executor

    def _check_preconditions(self, state: AgentState) -> str | None:
        if not state.get("sql_is_safe"):
            return "SQL did not pass guardrail"
        if not state.get("generated_sql"):
            return "No SQL to execute"
        return None

    async def _run(self, state: AgentState) -> dict:
        rows = await self._executor.execute(state["generated_sql"])
        return {"query_result": rows, "error": None}
