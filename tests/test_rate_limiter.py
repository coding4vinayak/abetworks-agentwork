"""Tests for the rate limiter module."""

import time

import pytest

from agentwork.server.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test token bucket rate limiter."""

    @pytest.fixture
    def limiter(self):
        return RateLimiter(rate=10.0, capacity=5)

    def test_allows_within_capacity(self, limiter):
        """Requests within capacity are allowed."""
        for _ in range(5):
            assert limiter.allow("client-1") is True

    def test_denies_after_capacity_exhausted(self, limiter):
        """Requests beyond capacity are denied."""
        for _ in range(5):
            limiter.allow("client-1")
        assert limiter.allow("client-1") is False

    def test_per_client_tracking(self, limiter):
        """Different clients have separate buckets."""
        for _ in range(5):
            limiter.allow("client-1")
        # client-1 exhausted, but client-2 is fresh
        assert limiter.allow("client-1") is False
        assert limiter.allow("client-2") is True

    def test_tokens_refill_over_time(self):
        """Tokens refill at the specified rate."""
        limiter = RateLimiter(rate=100.0, capacity=2)
        # Exhaust the bucket
        limiter.allow("client-1")
        limiter.allow("client-1")
        assert limiter.allow("client-1") is False
        # Wait for refill (100 tokens/sec = 0.01 sec per token)
        time.sleep(0.02)
        assert limiter.allow("client-1") is True

    def test_get_retry_after_when_allowed(self, limiter):
        """get_retry_after returns 0 when tokens available."""
        assert limiter.get_retry_after("fresh-client") == 0.0

    def test_get_retry_after_when_denied(self, limiter):
        """get_retry_after returns positive float when bucket empty."""
        for _ in range(5):
            limiter.allow("client-1")
        retry_after = limiter.get_retry_after("client-1")
        assert retry_after > 0.0

    def test_reset_specific_client(self, limiter):
        """reset(client_id) clears that client's bucket."""
        for _ in range(5):
            limiter.allow("client-1")
        assert limiter.allow("client-1") is False
        limiter.reset("client-1")
        assert limiter.allow("client-1") is True

    def test_reset_all_clients(self, limiter):
        """reset() without args clears all buckets."""
        for _ in range(5):
            limiter.allow("client-1")
        for _ in range(5):
            limiter.allow("client-2")
        limiter.reset()
        assert limiter.allow("client-1") is True
        assert limiter.allow("client-2") is True

    def test_capacity_not_exceeded_by_refill(self):
        """Tokens do not exceed capacity even after long idle periods."""
        limiter = RateLimiter(rate=1000.0, capacity=3)
        # First request after a long time should not have more than capacity tokens
        time.sleep(0.01)
        assert limiter.allow("client-1") is True
        assert limiter.allow("client-1") is True
        assert limiter.allow("client-1") is True
        # Should be denied now since capacity is 3
        assert limiter.allow("client-1") is False
