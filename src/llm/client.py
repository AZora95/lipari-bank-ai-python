from typing import Protocol

from src.llm.types import LLMResponse, Message

from src.exceptions import AppError

__all__ = ["LLMProvider", "LLMProviderError", "LLMResponse", "Message"]


class LLMProviderError(AppError):
    """Raised when a provider call fails definitively (retries exhausted or non-retryable error)."""

    def __init__(self, provider: str, model: str, message: str) -> None:
        self.provider = provider
        self.model = model
        super().__init__(502, "LLM_PROVIDER_ERROR", f"[{provider}:{model}] {message}")



class LLMProvider(Protocol):
    """Unified async interface every LLM provider must implement."""

    async def complete(self, messages: list[Message], max_tokens: int = 500) -> LLMResponse: ...
