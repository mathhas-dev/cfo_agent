"""Composition root — wires all dependencies and compiles the LangGraph graph.

Dependency Inversion: this module owns all wiring. Lower-level modules
(nodes, db, schema_registry) never import from graph.py.

Graph flow:
    nl2sql → guardrail → [executor → response_builder] | [error_handler]
"""
from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from agent.llm_factory import get_llm
from agent.nodes.error_handler import ErrorHandlerNode
from agent.nodes.executor import ExecutorNode
from agent.nodes.guardrail import GuardrailNode
from agent.nodes.nl2sql import NL2SqlNode
from agent.nodes.response_builder import ResponseBuilderNode
from agent.state import AgentState
from config import settings
from db.engine import build_engine
from db.executor import SqlExecutor
from schema_registry.registry import SchemaRegistry

_SCHEMA_PATH = Path(__file__).parent.parent / "schema_registry" / "schema.yaml"

NODE_NL2SQL    = "nl2sql"
NODE_GUARDRAIL = "guardrail"
NODE_EXECUTOR  = "executor"
NODE_RESPONSE  = "response_builder"
NODE_ERROR     = "error_handler"


def _route_after_guardrail(state: AgentState) -> str:
    if state.get("sql_is_safe"):
        return NODE_EXECUTOR
    return NODE_ERROR


def build_graph():
    """Builds and compiles the CFOAgent graph.

    Call once at startup — the compiled graph is thread-safe and reusable.
    MemorySaver persists session state in-process (dev).
    Swap for SqliteSaver or a remote checkpointer in prod.
    """
    llm = get_llm()
    engine = build_engine(settings.db_connection_string.get_secret_value())
    sql_executor = SqlExecutor(engine)
    schema = SchemaRegistry.from_file(_SCHEMA_PATH)

    builder = StateGraph(AgentState)

    builder.add_node(NODE_NL2SQL,    NL2SqlNode(llm=llm, schema=schema))
    builder.add_node(NODE_GUARDRAIL, GuardrailNode())
    builder.add_node(NODE_EXECUTOR,  ExecutorNode(executor=sql_executor))
    builder.add_node(NODE_RESPONSE,  ResponseBuilderNode())
    builder.add_node(NODE_ERROR,     ErrorHandlerNode())

    builder.set_entry_point(NODE_NL2SQL)
    builder.add_edge(NODE_NL2SQL, NODE_GUARDRAIL)
    builder.add_conditional_edges(NODE_GUARDRAIL, _route_after_guardrail)
    builder.add_edge(NODE_EXECUTOR, NODE_RESPONSE)
    builder.add_edge(NODE_RESPONSE, END)
    builder.add_edge(NODE_ERROR,    END)

    return builder.compile(checkpointer=MemorySaver())
