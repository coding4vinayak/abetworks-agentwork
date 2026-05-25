"""LLM provider abstraction - base classes and response models."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator

from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    """Token usage statistics for an LLM response."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMResponse(BaseModel):
    """Response from an LLM provider."""

    content: str = ""
    model: str = ""
    usage: TokenUsage = Field(default_factory=TokenUsage)
    cost: float = 0.0
    metadata: dict = Field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    Subclasses must implement complete, complete_async, stream, and get_token_count.
    """

    @abstractmethod
    def complete(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Generate a completion for the given prompt."""
        ...

    @abstractmethod
    async def complete_async(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Generate a completion asynchronously."""
        ...

    @abstractmethod
    async def stream(self, prompt: str, **kwargs: Any) -> AsyncGenerator[str, None]:
        """Stream completion chunks for the given prompt."""
        ...

    @abstractmethod
    def get_token_count(self, text: str) -> int:
        """Estimate the token count for the given text."""
        ...
