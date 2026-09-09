import logging

from anthropic import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncAnthropic,
    RateLimitError,
)
from anthropic.types import Message as AnthropicMessage
from anthropic.types import MessageParam, TextBlock
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.llm.client import LLMProviderError
from src.llm.types import LLMResponse, Message

logger = logging.getLogger(__name__)

_RETRYABLE_ERRORS = (RateLimitError, APIConnectionError, APITimeoutError)


class AnthropicProvider:
    """Anthropic messages provider with cost tracking and retry-with-backoff.

    Anthropic's API takes `system` as a separate top-level argument rather than
    a message with role="system", unlike OpenAI's unified messages array.
    """

    PROVIDER_NAME = "anthropic"

    # EUR per 1k tokens: (input, output)
    PRICING: dict[str, tuple[float, float]] = {
        "claude-haiku-4-5-20251001": (0.000226, 0.001129),
        "claude-sonnet-4-6": (0.00271, 0.01355),
    }

    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001") -> None:
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def complete(self, messages: list[Message], max_tokens: int = 500) -> LLMResponse:
        system = "\n".join(m.content for m in messages if m.role == "system")
        user_messages: list[MessageParam] = [
            {"role": m.role, "content": m.content}  # type: ignore[typeddict-item]
            for m in messages
            if m.role != "system"
        ]

        try:
            response = await self._create(system, user_messages, max_tokens)
        except _RETRYABLE_ERRORS as exc:
            raise LLMProviderError(
                self.PROVIDER_NAME, self.model, f"retries exhausted: {exc}"
            ) from exc
        except APIStatusError as exc:
            raise LLMProviderError(
                self.PROVIDER_NAME, self.model, f"API error {exc.status_code}: {exc.message}"
            ) from exc

        text_block = next((b for b in response.content if isinstance(b, TextBlock)), None)
        if text_block is None:
            raise LLMProviderError(
                self.PROVIDER_NAME, self.model, "response contained no text block"
            )

        usage = response.usage
        return LLMResponse(
            content=text_block.text,
            tokens_used=usage.input_tokens + usage.output_tokens,
            cost_eur=self._compute_cost(usage.input_tokens, usage.output_tokens),
            model=self.model,
        )

    @retry(
        retry=retry_if_exception_type(_RETRYABLE_ERRORS),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _create(
        self, system: str, user_messages: list[MessageParam], max_tokens: int
    ) -> AnthropicMessage:
        return await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=user_messages,
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
