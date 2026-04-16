"""Dev entry point — REPL loop for testing the agent without Teams.

For Teams deployment, use teams/adapter.py with Bot Framework SDK.
Requires Ollama running locally: ollama run qwen2.5-coder:14b
"""
import asyncio

from langchain_core.messages import HumanMessage

from agent.graph import build_graph

_REPL_THREAD_ID = "dev-session-001"


async def main() -> None:
    graph = build_graph()
    config = {"configurable": {"thread_id": _REPL_THREAD_ID}}

    print("CFOAgent ready. Type 'exit' to quit.\n")
    while True:
        question = input("You: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue

        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=question)]},
            config=config,
        )
        print(f"\nAgent:\n{result['messages'][-1].content}\n")


if __name__ == "__main__":
    asyncio.run(main())
