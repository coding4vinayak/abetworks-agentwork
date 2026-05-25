"""Tests for resilience patterns."""

import time
import pytest

from agentwork import RetryPolicy, FallbackChain, CircuitBreaker, Timeout
from agentwork.core.exceptions import RetryableError, AgentError, TimeoutError


class TestRetryPolicy:
    def test_successful_execution(self):
        policy = RetryPolicy(max_attempts=3)
        result = policy.execute(lambda: "success")
        assert result == "success"

    def test_retry_on_failure(self):
        call_count = {"n": 0}

        def flaky():
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise ValueError("not yet")
            return "finally"

        policy = RetryPolicy(max_attempts=3, backoff_base=0.01, jitter=0)
        result = policy.execute(flaky)
        assert result == "finally"
        assert call_count["n"] == 3

    def test_all_retries_exhausted(self):
        def always_fails():
            raise ValueError("always")

        policy = RetryPolicy(max_attempts=2, backoff_base=0.01, jitter=0)
        with pytest.raises(RetryableError) as exc_info:
            policy.execute(always_fails)
        assert "exhausted" in str(exc_info.value)

    def test_on_retry_callback(self):
        errors = []

        def on_retry(e):
            errors.append(str(e))

        call_count = {"n": 0}

        def flaky():
            call_count["n"] += 1
            if call_count["n"] < 2:
                raise ValueError("oops")
            return "ok"

        policy = RetryPolicy(max_attempts=3, backoff_base=0.01, jitter=0, on_retry=on_retry)
        policy.execute(flaky)
        assert len(errors) == 1


class TestFallbackChain:
    def test_first_succeeds(self):
        chain = FallbackChain(strategies=[lambda: "first", lambda: "second"])
        assert chain.execute() == "first"

    def test_fallback_to_second(self):
        def fail():
            raise ValueError("fail")

        chain = FallbackChain(strategies=[fail, lambda: "backup"])
        assert chain.execute() == "backup"

    def test_all_fail_with_default(self):
        def fail():
            raise ValueError("fail")

        chain = FallbackChain(strategies=[fail, fail], default="safe_value")
        assert chain.execute() == "safe_value"

    def test_all_fail_no_default(self):
        def fail():
            raise ValueError("fail")

        chain = FallbackChain(strategies=[fail, fail])
        with pytest.raises(AgentError):
            chain.execute()

    def test_add_strategy(self):
        chain = FallbackChain()
        chain.add(lambda: "added")
        assert chain.execute() == "added"


class TestCircuitBreaker:
    def test_closed_state(self):
        breaker = CircuitBreaker(failure_threshold=3)
        assert breaker.is_closed
        result = breaker.execute(lambda: "ok")
        assert result == "ok"

    def test_opens_after_threshold(self):
        breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=60)

        def fail():
            raise ValueError("err")

        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.execute(fail)

        assert breaker.is_open

        # Subsequent calls are rejected
        with pytest.raises(AgentError) as exc_info:
            breaker.execute(lambda: "should not execute")
        assert "OPEN" in str(exc_info.value)

    def test_half_open_after_cooldown(self):
        breaker = CircuitBreaker(failure_threshold=1, cooldown_seconds=0.01)

        def fail():
            raise ValueError("err")

        with pytest.raises(ValueError):
            breaker.execute(fail)

        assert breaker.is_open
        time.sleep(0.02)
        # Should transition to half-open
        assert breaker.state.value == "half_open"

    def test_reset(self):
        breaker = CircuitBreaker(failure_threshold=1)

        def fail():
            raise ValueError("err")

        with pytest.raises(ValueError):
            breaker.execute(fail)

        breaker.reset()
        assert breaker.is_closed


class TestTimeout:
    def test_within_timeout(self):
        timeout = Timeout(seconds=5.0)
        result = timeout.execute(lambda: "fast")
        assert result == "fast"

    def test_exceeds_timeout(self):
        timeout = Timeout(seconds=0.05)

        def slow():
            time.sleep(1.0)
            return "slow"

        with pytest.raises(TimeoutError):
            timeout.execute(slow)

    def test_invalid_timeout(self):
        with pytest.raises(ValueError):
            Timeout(seconds=0)

        with pytest.raises(ValueError):
            Timeout(seconds=-1)
