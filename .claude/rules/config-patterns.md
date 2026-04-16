## Config & Environment Patterns

### Single source of truth: BaseSettings
All configuration lives in one `config.py`. Never read `os.environ` directly in business logic.

```python
from pydantic_settings import BaseSettings
from pydantic import SecretStr

class Settings(BaseSettings):
    llm_provider: str = "ollama"           # "ollama" | "azure_openai" | "anthropic"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:14b"
    azure_openai_endpoint: str = ""
    azure_openai_api_key: SecretStr = SecretStr("")
    azure_openai_deployment: str = ""
    anthropic_api_key: SecretStr = SecretStr("")
    anthropic_model: str = "claude-sonnet-4-6"
    db_connection_string: SecretStr                # required, no default
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()
```

### LLM factory — dev/prod switch
```python
from langchain_core.language_models import BaseChatModel

def get_llm() -> BaseChatModel:
    if settings.llm_provider == "ollama":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(base_url=settings.ollama_base_url, model=settings.ollama_model)
    elif settings.llm_provider == "azure_openai":
        from langchain_openai import AzureChatOpenAI
        return AzureChatOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key.get_secret_value(),
            azure_deployment=settings.azure_openai_deployment,
        )
    elif settings.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            api_key=settings.anthropic_api_key.get_secret_value(),
            model=settings.anthropic_model,
        )
    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider}")
```

### Env files
- `.env` — local dev values (gitignored)
- `.env.example` — template with placeholder values, committed
- Never commit `.env` or any file containing real secrets

### Docker / Container Apps
Pass secrets as environment variables via Azure Key Vault references or GitHub Actions secrets — never bake them into the image.
