from decimal import Decimal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "LipariBank AI"
    debug: bool = False

    database_url: str
    openai_api_key: str
    anthropic_api_key: str
    opencode_api_key: str
    default_model: str = "big-pickle"
    embedding_model: str = "nomic-embed-text"
    ollama_base_url: str = "http://localhost:11434"
    # l'agente usa un modello locale di Ollama, via l'API compatibile OpenAI: servono i tool
    agent_model: str = "qwen2.5:7b"
    max_tokens_per_request: int = 2000
    jwt_secret: str
    soglia_approvazione_eur: Decimal = Decimal("5000")  # sopra, decide una persona


settings = Settings()  # raise at import if missing required
