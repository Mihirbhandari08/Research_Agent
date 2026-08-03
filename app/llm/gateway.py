"""
app/llm/gateway.py
==================
Convenience gateway for constructing provider-backed LLM clients from the shared run context.
"""

from __future__ import annotations

from typing import Any, Type, TypeVar

from pydantic import BaseModel

from app.config.settings import get_settings
from app.harness.context import RunContext
from app.llm.base import BaseLLMClient, LLMMessage, LLMResponse
from app.llm.litellm_client import LiteLLMClient

T = TypeVar("T", bound=BaseModel)


class LLMGateway:
    """Thin factory and facade around the configured provider implementation."""

    def __init__(self, context: RunContext, model: str | None = None) -> None:
        settings = get_settings()
        self.context = context
        self.model = model or settings.llm.gemini_default_model
        self._client = LiteLLMClient(context=context, model=self.model)

    def client(self, model: str | None = None) -> BaseLLMClient:
        if model is None:
            return self._client
        return LiteLLMClient(context=self.context, model=model)

    async def generate(
        self,
        messages: list[LLMMessage],
        node: str,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        return await self._client.generate(
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
        return await self._client.generate_structured(
            messages=messages,
            response_model=response_model,
            node=node,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )


def get_default_llm_gateway(context: RunContext, model: str | None = None) -> LLMGateway:
    """Create a gateway using the app's default Gemini model unless overridden."""
    return LLMGateway(context=context, model=model)
