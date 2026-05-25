"""Anthropic LLM provider (stub implementation)."""

from __future__ import annotations

from typing import Any, AsyncGenerator

from agentwork.llm.providers import LLMProvider, LLMResponse, TokenUsage


class AnthropicProvider(LLMProvider):
    """Anthropic LLM provider.

    This is a stub implementation that demonstrates the interface
    without making real HTTP calls. Replace with actual API calls
    for production use.
    """

    def __init__(
        self,
        api_key: str = "",
        model: str = "claude-3-sonnet-20240229",
    ) -> None:
        self.api_key = api_key
        self.model = model

    def complete(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Return a stub LLMResponse for the given prompt."""
        prompt_tokens = self.get_token_count(prompt)
        content = f"[Anthropic stub response for: {prompt[:50]}]"
        completion_tokens = self.get_token_count(content)

        return LLMResponse(
            content=content,
            model=self.model,
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            cost=0.0,
            metadata={"provider": "anthropic"},
        )

    async def complete_async(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Return a stub LLMResponse asynchronously."""
        return self.complete(prompt, **kwargs)

    async def stream(self, prompt: str, **kwargs: Any) -> AsyncGenerator[str, None]:
        """Yield stub chunks for the given prompt."""
        chunks = [
            f"[Anthropic stream chunk 1 for: {prompt[:30]}]",
            "[Anthropic stream chunk 2]",
            "[Anthropic stream chunk 3]",
            "[Anthropic stream end]",
        ]
        for chunk in chunks:
            yield chunk

    def get_token_count(self, text: str) -> int:
        """Estimate token count using word-based approximation."""
        return len(text.split()) * 4 // 3
