"""Observer pattern — audit logging via LangChain callbacks.

Registered at graph build time so nodes stay clean.
All LLM interactions are logged here for the audit trail.
"""
import structlog
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult

logger = structlog.get_logger(__name__)


class AuditCallbackHandler(AsyncCallbackHandler):
    """Logs LLM-generated content without polluting node business logic."""

    async def on_llm_end(self, response: LLMResult, **kwargs: object) -> None:
        try:
            generated_text = response.generations[0][0].text
            logger.info("llm_output_generated", content_preview=generated_text[:300])
        except (IndexError, AttributeError):
            logger.warning(
                "audit_log_failed",
                reason="unexpected LLM response structure",
            )
