"""
app/llm/litellm_client.py
=========================
Concrete LiteLLM adapter implementing BaseLLMClient.
Handles Gemini 2.5 Pro calls with retry, budget enforcement, tracing, and metrics.
"""

import time
from typing import Any, Type, TypeVar

import litellm

from app.domain import TokenUsage
from app.harness.context import RunContext
from app.harness.exceptions import LLMRateLimitError
from app.harness.retry import RetryExecutor, RetryPolicy
from app.llm.base import BaseLLMClient, LLMMessage, LLMResponse
from app.llm.parser import parse_llm_output
from app.observability.logging import get_logger
from app.observability.metrics import metrics
from app.observability.tracing import async_node_span

logger = get_logger(__name__)

T = TypeVar("T")

# Exception types that are transient and safe to retry
_RETRYABLE_EXCEPTIONS = (LLMRateLimitError, litellm.RateLimitError, litellm.Timeout)


class LiteLLMClient(BaseLLMClient):
    """
    LiteLLM-backed LLM client that routes calls through Gemini 2.5 Pro by default.

    Automatically handles:
    - Budget guard checks before invocation
    - Exponential backoff retry on rate limits
    - Token usage tracking via RunContext
    - Prometheus metric emission
    - OTEL distributed tracing spans
    """

    def __init__(
        self,
        context: RunContext,
        model: str | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self.context = context
        self.model = model or self._default_model()
        self._retry = RetryExecutor(retry_policy or RetryPolicy())

    def _default_model(self) -> str:
        """Reads the default model from settings."""
        from app.config.settings import get_settings
        return get_settings().llm.gemini_default_model

    async def generate(
        self,
        messages: list[LLMMessage],
        node: str,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generates a free-form text completion via LiteLLM.

        Raises:
            BudgetExhaustedError: If budget limits are exceeded before the call.
            LLMRateLimitError: If rate limit retries are exhausted.
        """
        # Pre-call guard check
        self.context.verify_guards()

        return await self._retry.execute(
            self._call_litellm,
            _RETRYABLE_EXCEPTIONS,
            messages=messages,
            node=node,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    async def generate_structured(
        self,
        messages: list[LLMMessage],
        response_model: Type[T],
        node: str,
        temperature: float = 0.1,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> T:
        """
        Generates a Pydantic-validated structured JSON completion.

        Raises:
            LLMOutputParseError: If the model output fails schema validation.
            BudgetExhaustedError: If budget limits are exceeded before the call.
        """
        # Inject JSON instruction into the last user message
        structured_messages = _inject_json_instruction(messages, response_model)

        llm_response = await self.generate(
            messages=structured_messages,
            node=node,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        return parse_llm_output(
            raw=llm_response.content,
            response_model=response_model,
            node=node,
            model_name=self.model,
        )

    async def _call_litellm(
        self,
        messages: list[LLMMessage],
        node: str,
        temperature: float,
        max_tokens: int | None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Internal method making the raw LiteLLM API call with telemetry.
        """
        raw_messages = [m.to_dict() for m in messages]
        call_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": raw_messages,
            "temperature": temperature,
        }
        if max_tokens:
            call_kwargs["max_tokens"] = max_tokens
        call_kwargs.update(kwargs)

        start = time.monotonic()

        async with async_node_span(f"llm.{node}", run_id=self.context.run_id, model=self.model):
            try:
                response = await litellm.acompletion(**call_kwargs)
            except litellm.RateLimitError as exc:
                logger.warning(
                    "LLM rate limit hit.",
                    node=node,
                    model=self.model,
                    run_id=self.context.run_id,
                )
                raise LLMRateLimitError(
                    message=f"Rate limited by {self.model}: {exc}",
                    model_name=self.model,
                    run_id=self.context.run_id,
                ) from exc

        duration = time.monotonic() - start

        # Extract token usage from response
        usage = response.usage or {}
        prompt_tokens = getattr(usage, "prompt_tokens", 0)
        completion_tokens = getattr(usage, "completion_tokens", 0)
        cost = litellm.completion_cost(response) if hasattr(litellm, "completion_cost") else 0.0

        # Record metrics and update RunContext
        self.context.record_llm_call(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost,
        )
        metrics.record_llm_call(
            model=self.model,
            node=node,
            duration=duration,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost,
        )

        content = response.choices[0].message.content or ""

        logger.info(
            "LLM call completed.",
            node=node,
            model=self.model,
            run_id=self.context.run_id,
            duration_s=round(duration, 3),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=round(cost, 6),
        )

        return LLMResponse(
            content=content,
            model=self.model,
            token_usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                estimated_cost_usd=cost,
            ),
            raw=response,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _inject_json_instruction(messages: list[LLMMessage], response_model: Any) -> list[LLMMessage]:
    """
    Appends a JSON schema instruction to the last user message to guide structured output.
    """
    schema = response_model.model_json_schema()
    instruction = (
        f"\n\nRespond ONLY with a valid JSON object matching this schema. "
        f"No markdown, no explanation, only JSON.\n\nSchema:\n{schema}"
    )

    # Clone messages to avoid mutating the caller's list
    updated = list(messages)
    if updated and updated[-1].role == "user":
        last = updated[-1]
        updated[-1] = LLMMessage.user(last.content + instruction)
    else:
        updated.append(LLMMessage.user(instruction))

    return updated
