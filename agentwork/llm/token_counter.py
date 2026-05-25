"""Token counting and cost estimation utilities."""

from __future__ import annotations

from typing import Dict, Tuple


class TokenCounter:
    """Utility for estimating token counts and costs for LLM calls.

    Uses word-based approximation for token estimation and a price table
    for cost calculation.
    """

    # Price table: model -> (prompt_price_per_1k, completion_price_per_1k)
    PRICE_TABLE: Dict[str, Tuple[float, float]] = {
        "gpt-4": (0.03, 0.06),
        "gpt-3.5-turbo": (0.0015, 0.002),
        "claude-3-sonnet": (0.003, 0.015),
        "claude-3-opus": (0.015, 0.075),
    }

    def estimate_tokens(self, text: str, model: str = "gpt-4") -> int:
        """Estimate the number of tokens in the given text.

        Uses a rough approximation: words * 4/3 + 1.
        """
        return len(text.split()) * 4 // 3 + 1

    def estimate_cost(
        self, prompt_tokens: int, completion_tokens: int, model: str = "gpt-4"
    ) -> float:
        """Estimate the cost of a completion based on token counts.

        Returns 0.0 if the model is not in the price table.
        """
        if model not in self.PRICE_TABLE:
            return 0.0

        prompt_price, completion_price = self.PRICE_TABLE[model]
        cost = (prompt_tokens / 1000.0) * prompt_price + (
            completion_tokens / 1000.0
        ) * completion_price
        return cost
