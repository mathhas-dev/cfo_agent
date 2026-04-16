Scaffold a new LangGraph node.

Steps:
1. Ask the user: node name and what state fields it reads and writes.
2. Create `agent/nodes/<node_name>.py` with:
   - Async function signature `async def <node_name>_node(state: AgentState) -> dict:`
   - Reads only the state fields listed
   - Returns a dict with only the fields it writes
   - All errors caught and written to `state["error"]` — no unhandled exceptions
   - Type hints on the function signature
3. Add a unit test stub in `tests/unit/test_<node_name>_node.py`.
4. Show where to wire the node into `agent/graph.py` (but do not edit the graph file — let the user decide the edge logic).
