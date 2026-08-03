"""
app/llm/base.py
===============
Abstract base class defining the interface all LLM provider adapters must implement.
Decouples graph nodes from any specific model provider (Gemini, OpenAI, Anthropic, etc.).
"""

from abc import ABC, abstractmethod
from typing import Any, Type, TypeVar

from pydantic import BaseModel

from app.domain import TokenUsage

T = TypeVar("T", bound=BaseModel)


class LLMMessage:
    """A single message in the conversation history."""

    def __init__(self, role: str, content: str) -> None:
        if role not in ("system", "user", "assistant"):
            raise ValueError(f"Invalid role '{role}'. Must be 'system', 'user', or 'assistant'.")
        self.role = role
        self.content = content

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}

    @classmethod
    def system(cls, content: str) -> "LLMMessage":
        return cls(role="system", content=content)

    @classmethod
    def user(cls, content: str) -> "LLMMessage":
        return cls(role="user", content=content)

    @classmethod
    def assistant(cls, content: str) -> "LLMMessage":
        return cls(role="assistant", content=content)


class LLMResponse:
    """The structured response returned by any LLM gateway call."""

    def __init__(
        self,
        content: str,
        model: str,
        token_usage: TokenUsage,
        raw: Any = None,
    ) -> None:
        self.content = content
        self.model = model
        self.token_usage = token_usage
        self.raw = raw  # Original API response object for debugging


class BaseLLMClient(ABC):
    """
    Abstract base class all concrete LLM adapters (LiteLLM, OpenAI, etc.) must implement.
    
    Enforces a consistent calling contract so graph nodes and prompt builders
    are completely provider-agnostic.
    """

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        node: str,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generates a free-form text completion.

        Args:
            messages: The conversation history (system + user turns).
            node: Name of the graph node making this call (for telemetry).
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative).
            max_tokens: Maximum number of completion tokens.

        Returns:
            LLMResponse: Completed text, model name, and token usage.
        """
        ...

    @abstractmethod
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
        Generates a structured JSON completion validated against a Pydantic model.

        Args:
            messages: The conversation history (system + user turns).
            response_model: The Pydantic class the JSON response should validate against.
            node: Name of the graph node making this call (for telemetry).
            temperature: Sampling temperature (lower = more deterministic JSON outputs).
            max_tokens: Maximum completion tokens.

        Returns:
            T: A validated instance of the specified Pydantic response_model.
        
        Raises:
            LLMOutputParseError: If the model output fails Pydantic validation.
        """
        ...
