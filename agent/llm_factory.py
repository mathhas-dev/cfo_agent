"""Factory Method + Strategy — LLM provider selection.

Nodes depend on BaseChatModel (abstraction).
This module owns the concrete construction logic.
Add a new provider by adding a builder function and registering it in _PROVIDER_BUILDERS.
"""
from langchain_core.language_models import BaseChatModel

from agent.audit import AuditCallbackHandler
from config import settings

LLM_PROVIDER_OLLAMA = "ollama"
LLM_PROVIDER_AZURE_OPENAI = "azure_openai"
LLM_PROVIDER_ANTHROPIC = "anthropic"


def get_llm() -> BaseChatModel:
    """Returns the correct LLM for the current environment.

    Strategy selector: LLM_PROVIDER env var determines which concrete
    BaseChatModel is returned. Callers depend only on BaseChatModel.
    """
    builder = _PROVIDER_BUILDERS.get(settings.llm_provider)
    if not builder:
        raise ValueError(
            f"Unknown LLM provider: {settings.llm_provider!r}. "
            f"Valid options: {list(_PROVIDER_BUILDERS)}"
        )
    llm = builder()
    # Attach audit observer without modifying the LLM object itself
    return llm.with_config(callbacks=[AuditCallbackHandler()])


def _build_ollama() -> BaseChatModel:
    from langchain_community.chat_models import ChatOllama

    return ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
    )


def _build_azure_openai() -> BaseChatModel:
    from langchain_openai import AzureChatOpenAI

    return AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key.get_secret_value(),
        azure_deployment=settings.azure_openai_deployment,
    )


def _build_anthropic() -> BaseChatModel:
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        api_key=settings.anthropic_api_key.get_secret_value(),
        model=settings.anthropic_model,
    )


# Open for extension: add a new provider without touching existing builders
_PROVIDER_BUILDERS: dict[str, callable] = {
    LLM_PROVIDER_OLLAMA: _build_ollama,
    LLM_PROVIDER_AZURE_OPENAI: _build_azure_openai,
    LLM_PROVIDER_ANTHROPIC: _build_anthropic,
}
