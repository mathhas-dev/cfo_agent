## LangGraph Patterns

### State definition
Define state as a typed `TypedDict`. Every field must have a clear owner (which node writes it).

```python
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]  # conversation history
    generated_sql: str | None               # written by nl2sql node
    sql_is_safe: bool | None                # written by guardrail node
    query_result: list[dict] | None         # written by executor node
    error: str | None                       # set by any node on failure
```

### Node contract
Each node function:
- Takes `AgentState`, returns `dict` with only the fields it updates
- Raises no exceptions — catches and writes to `state["error"]`
- Is async if it makes any I/O call

```python
async def nl2sql_node(state: AgentState) -> dict:
    # only writes generated_sql
    ...
    return {"generated_sql": sql, "error": None}
```

### Conditional routing
Use `add_conditional_edges` for guardrail branching — never if/else inside a node to decide the next step.

```python
graph.add_conditional_edges(
    "guardrail",
    lambda s: "executor" if s["sql_is_safe"] else "error_handler",
)
```

### Session memory
Use LangGraph's built-in checkpointer (`MemorySaver` in dev, `SqliteSaver` or Azure-backed in prod). Pass `thread_id` = Teams conversation ID so state persists across turns.

```python
from langgraph.checkpoint.memory import MemorySaver

graph = builder.compile(checkpointer=MemorySaver())

config = {"configurable": {"thread_id": activity.conversation.id}}
result = await graph.ainvoke({"messages": [user_msg]}, config=config)
```

### Don't put business logic in the graph definition
The `StateGraph` builder file only wires nodes and edges. Business logic lives in the node functions in their own modules.

### Schema injection
Schema context is injected at the `nl2sql` node level, not at graph construction time. This allows per-question schema filtering (relevant tables only) without rebuilding the graph.
