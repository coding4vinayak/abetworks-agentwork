"""Tests for review fixes: LRU eviction, true parallel, jitter, auto-health, default auth."""

import asyncio
import time
import threading
from unittest.mock import patch, MagicMock

import pytest

from agentwork import Agent, FleetManager, Pipeline, RetryPolicy, tool
from agentwork.core.result import TaskResult, ResultStatus
from agentwork.server.app import LRUResultStore, TaskResponse, create_app


class TestLRUResultStore:
    """Tests for bounded result store with LRU eviction."""

    def test_basic_put_and_get(self):
        store = LRUResultStore(max_size=5)
        resp = TaskResponse(task_id="t1", status="success", output="data")
        store.put("t1", resp)
        assert store.get("t1") == resp

    def test_eviction_at_max_size(self):
        store = LRUResultStore(max_size=3)
        for i in range(5):
            resp = TaskResponse(task_id=f"t{i}", status="success")
            store.put(f"t{i}", resp)

        # Oldest entries (t0, t1) should be evicted
        assert store.get("t0") is None
        assert store.get("t1") is None
        # Newest entries should remain
        assert store.get("t2") is not None
        assert store.get("t3") is not None
        assert store.get("t4") is not None
        assert len(store) == 3

    def test_access_refreshes_entry(self):
        store = LRUResultStore(max_size=3)
        for i in range(3):
            resp = TaskResponse(task_id=f"t{i}", status="success")
            store.put(f"t{i}", resp)

        # Access t0 to move it to end (most recently used)
        store.get("t0")

        # Add two more entries - should evict t1 and t2 (oldest unused)
        store.put("t3", TaskResponse(task_id="t3", status="success"))
        store.put("t4", TaskResponse(task_id="t4", status="success"))

        # t0 should still be there (was accessed recently)
        assert store.get("t0") is not None
        # t1 and t2 should be evicted
        assert store.get("t1") is None
        assert store.get("t2") is None

    def test_contains(self):
        store = LRUResultStore(max_size=5)
        store.put("t1", TaskResponse(task_id="t1", status="success"))
        assert "t1" in store
        assert "t2" not in store

    def test_keys(self):
        store = LRUResultStore(max_size=5)
        store.put("t1", TaskResponse(task_id="t1", status="success"))
        store.put("t2", TaskResponse(task_id="t2", status="success"))
        assert set(store.keys()) == {"t1", "t2"}

    def test_overwrite_existing_key(self):
        store = LRUResultStore(max_size=3)
        store.put("t1", TaskResponse(task_id="t1", status="success", output="old"))
        store.put("t1", TaskResponse(task_id="t1", status="success", output="new"))
        assert store.get("t1").output == "new"
        assert len(store) == 1


class TestCreateAppWithApiKeys:
    """Tests for create_app with api_keys parameter."""

    def test_create_app_without_api_keys(self):
        agent = Agent(name="TestAgent")
        app = create_app(agent)
        assert app is not None

    def test_create_app_with_api_keys(self):
        agent = Agent(name="TestAgent")
        app = create_app(agent, api_keys=["key1", "key2"])
        assert app is not None

    def test_create_app_with_max_results(self):
        agent = Agent(name="TestAgent")
        app = create_app(agent, max_results=100)
        assert app is not None


class TestTrueParallelExecution:
    """Tests that run_parallel actually executes tools concurrently."""

    def test_parallel_basic_results(self):
        @tool(name="a", description="A")
        def a(val: int) -> int:
            return val + 1

        @tool(name="b", description="B")
        def b(val: int) -> int:
            return val + 2

        pipeline = Pipeline(tools=[a, b])
        result = pipeline.run_parallel({"val": 10})
        assert result.success
        assert 11 in result.output
        assert 12 in result.output

    def test_parallel_actually_concurrent(self):
        """Verify tools run concurrently by checking timing."""
        sleep_time = 0.2

        @tool(name="slow_a", description="Slow A")
        def slow_a() -> str:
            time.sleep(sleep_time)
            return "a"

        @tool(name="slow_b", description="Slow B")
        def slow_b() -> str:
            time.sleep(sleep_time)
            return "b"

        @tool(name="slow_c", description="Slow C")
        def slow_c() -> str:
            time.sleep(sleep_time)
            return "c"

        pipeline = Pipeline(tools=[slow_a, slow_b, slow_c])
        start = time.time()
        result = pipeline.run_parallel()
        elapsed = time.time() - start

        assert result.success
        assert len(result.output) == 3
        # If truly parallel, total time should be ~sleep_time, not 3*sleep_time
        # Allow some overhead but it should be well under 2*sleep_time
        assert elapsed < sleep_time * 2.5, (
            f"Expected parallel execution under {sleep_time * 2.5}s, got {elapsed:.2f}s"
        )

    def test_parallel_preserves_order(self):
        """Results should be in the same order as tools, even if they finish out of order."""

        @tool(name="first", description="First")
        def first() -> str:
            time.sleep(0.15)
            return "first"

        @tool(name="second", description="Second")
        def second() -> str:
            return "second"

        pipeline = Pipeline(tools=[first, second])
        result = pipeline.run_parallel()
        assert result.success
        assert result.output == ["first", "second"]

    def test_parallel_with_failures(self):
        @tool(name="good", description="Good")
        def good(val: int) -> int:
            return val + 1

        @tool(name="bad", description="Bad")
        def bad(val: int) -> int:
            raise ValueError("broken")

        pipeline = Pipeline(tools=[good, bad])
        result = pipeline.run_parallel({"val": 10})
        assert result.status == ResultStatus.PARTIAL
        assert 11 in result.output


class TestAsyncRetryJitter:
    """Tests that async retry includes jitter in backoff calculation."""

    def test_async_retry_includes_jitter(self):
        """Verify jitter is applied by checking wait times vary."""
        call_count = {"n": 0}
        sleep_times = []

        async def flaky():
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise ValueError("not yet")
            return "done"

        original_sleep = asyncio.sleep

        async def mock_sleep(duration):
            sleep_times.append(duration)
            # Don't actually sleep in tests
            return

        policy = RetryPolicy(
            max_attempts=3, backoff_base=1.0, backoff_max=60.0, jitter=2.0
        )

        async def run():
            with patch("asyncio.sleep", side_effect=mock_sleep):
                return await policy.execute_async(flaky)

        result = asyncio.get_event_loop().run_until_complete(run())
        assert result == "done"
        # Should have slept twice (2 retries before success)
        assert len(sleep_times) == 2
        # Each sleep time should be base backoff + some jitter (0 to 2.0)
        # First attempt: base=1.0 * 2^0 = 1.0, plus jitter [0, 2.0]
        assert sleep_times[0] >= 1.0
        assert sleep_times[0] <= 3.0  # 1.0 + max jitter of 2.0
        # Second attempt: base=1.0 * 2^1 = 2.0, plus jitter [0, 2.0]
        assert sleep_times[1] >= 2.0
        assert sleep_times[1] <= 4.0  # 2.0 + max jitter of 2.0

    def test_async_retry_zero_jitter(self):
        """With jitter=0, backoff should be deterministic."""
        call_count = {"n": 0}
        sleep_times = []

        async def flaky():
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise ValueError("not yet")
            return "done"

        async def mock_sleep(duration):
            sleep_times.append(duration)
            return

        policy = RetryPolicy(
            max_attempts=3, backoff_base=0.5, backoff_max=60.0, jitter=0.0
        )

        async def run():
            with patch("asyncio.sleep", side_effect=mock_sleep):
                return await policy.execute_async(flaky)

        result = asyncio.get_event_loop().run_until_complete(run())
        assert result == "done"
        # With zero jitter, wait times should be exactly the base backoff
        assert sleep_times[0] == pytest.approx(0.5, abs=0.01)  # 0.5 * 2^0
        assert sleep_times[1] == pytest.approx(1.0, abs=0.01)  # 0.5 * 2^1


class TestFleetAutoHealth:
    """Tests for automatic health degradation after repeated failures."""

    def test_auto_marks_unhealthy_after_threshold(self):
        @tool(name="failing_tool", description="Always fails")
        def failing_tool() -> str:
            raise RuntimeError("broken")

        agent = Agent(name="FailAgent", tools=[failing_tool])
        fleet = FleetManager(failure_threshold=2)
        fleet.register(agent)

        # First failure
        result1 = fleet.dispatch("failing_tool")
        assert result1.failed
        assert fleet.pool.is_healthy("FailAgent")

        # Second failure - should trigger unhealthy
        result2 = fleet.dispatch("failing_tool")
        assert result2.failed
        assert not fleet.pool.is_healthy("FailAgent")

    def test_success_resets_failure_count(self):
        call_count = {"n": 0}

        @tool(name="flaky_tool", description="Sometimes fails")
        def flaky_tool() -> str:
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise RuntimeError("first fail")
            return "ok"

        agent = Agent(name="FlakyAgent", tools=[flaky_tool])
        fleet = FleetManager(failure_threshold=3)
        fleet.register(agent)

        # First call fails
        fleet.dispatch("flaky_tool")
        assert fleet._consecutive_failures["FlakyAgent"] == 1

        # Second call succeeds - should reset counter
        fleet.dispatch("flaky_tool")
        assert fleet._consecutive_failures["FlakyAgent"] == 0

    def test_mark_healthy_resets_counter(self):
        @tool(name="failing_tool", description="Fails")
        def failing_tool() -> str:
            raise RuntimeError("broken")

        agent = Agent(name="FailAgent", tools=[failing_tool])
        fleet = FleetManager(failure_threshold=2)
        fleet.register(agent)

        # Trigger auto-unhealthy
        fleet.dispatch("failing_tool")
        fleet.dispatch("failing_tool")
        assert not fleet.pool.is_healthy("FailAgent")

        # Manual recovery
        fleet.mark_healthy("FailAgent")
        assert fleet.pool.is_healthy("FailAgent")
        assert fleet._consecutive_failures["FailAgent"] == 0

    def test_default_threshold_is_three(self):
        fleet = FleetManager()
        assert fleet._failure_threshold == 3

    def test_custom_threshold(self):
        fleet = FleetManager(failure_threshold=5)
        assert fleet._failure_threshold == 5

    def test_unhealthy_agent_not_routed(self):
        @tool(name="work", description="Does work")
        def work() -> str:
            raise RuntimeError("broken")

        agent = Agent(name="Worker", tools=[work])
        fleet = FleetManager(failure_threshold=2)
        fleet.register(agent)

        # Trigger unhealthy
        fleet.dispatch("work")
        fleet.dispatch("work")
        assert not fleet.pool.is_healthy("Worker")

        # Next dispatch should fail with "no agent available"
        result = fleet.dispatch("work")
        assert result.failed
        assert "No agent available" in result.error
