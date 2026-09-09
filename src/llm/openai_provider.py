import logging

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    RateLimitError,
)
from openai.types.chat import ChatCompletion
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.llm.client import LLMProviderError
from src.llm.types import LLMResponse, Message

logger = logging.getLogger(__name__)

_RETRYABLE_ERRORS = (RateLimitError, APIConnectionError, APITimeoutError)


class OpenAIProvider:
    """OpenAI chat-completions provider with cost tracking and retry-with-backoff."""

    PROVIDER_NAME = "openai"

    # EUR per 1k tokens: (input, output)
    PRICING: dict[str, tuple[float, float]] = {
        "gpt-4o-mini": (0.00014, 0.00056),
        "gpt-4o": (0.0023, 0.0091),
    }

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def complete(self, messages: list[Message], max_tokens: int = 500) -> LLMResponse:
        try:
            response = await self._create(messages, max_tokens)
        except _RETRYABLE_ERRORS as exc:
            raise LLMProviderError(
                self.PROVIDER_NAME, self.model, f"retries exhausted: {exc}"
            ) from exc
        except APIStatusError as exc:
            raise LLMProviderError(
                self.PROVIDER_NAME, self.model, f"API error {exc.status_code}: {exc.message}"
            ) from exc

        usage = response.usage
        if usage is None:
            raise LLMProviderError(self.PROVIDER_NAME, self.model, "response missing usage data")

        return LLMResponse(
            content=response.choices[0].message.content or "",
            tokens_used=usage.total_tokens,
            cost_eur=self._compute_cost(usage.prompt_tokens, usage.completion_tokens),
            model=self.model,
        )

    @retry(
        retry=retry_if_exception_type(_RETRYABLE_ERRORS),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _create(self, messages: list[Message], max_tokens: int) -> ChatCompletion:
        return await self.client.chat.completions.create(
            model=self.model,
            messages=[m.model_dump() for m in messages],  # type: ignore[misc]
            max_tokens=max_tokens,
            temperature=0.3,
        )

    def _compute_cost(self, input_tokens: int, output_tokens: int) -> float:
        pricing = self.PRICING.get(self.model)
        if pricing is None:
            logger.warning(
                "no pricing entry for model %s; cost tracking defaults to 0.0", self.model
            )
            return 0.0
        input_cost, output_cost = pricing
        return (input_tokens * input_cost + output_tokens * output_cost) / 1000
