"""Teams Bot Framework adapter.

Single responsibility: translate Bot Framework Activities into LangGraph
invocations and send the reply back. No business logic lives here.
"""
import structlog
from botbuilder.core import ActivityHandler, TurnContext
from langchain_core.messages import HumanMessage

logger = structlog.get_logger(__name__)

_UNSUPPORTED_ACTIVITY_REPLY = "I only respond to text messages."


class CFOBotAdapter(ActivityHandler):
    def __init__(self, graph) -> None:
        self._graph = graph

    async def on_message_activity(self, turn_context: TurnContext) -> None:
        user_text = (turn_context.activity.text or "").strip()
        if not user_text:
            await turn_context.send_activity(_UNSUPPORTED_ACTIVITY_REPLY)
            return

        # Teams conversation ID is the natural session key for LangGraph state
        thread_id = turn_context.activity.conversation.id
        config = {"configurable": {"thread_id": thread_id}}

        logger.info("incoming_message", thread_id=thread_id, text_preview=user_text[:100])

        result = await self._graph.ainvoke(
            {"messages": [HumanMessage(content=user_text)]},
            config=config,
        )

        reply = result["messages"][-1].content
        await turn_context.send_activity(reply)
