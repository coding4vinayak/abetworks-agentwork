"""Tests for review fixes: LRU eviction, true parallel, jitter, auto-health, default auth,
bounded collections, thread safety, format-string injection prevention, async handler scheduling,
plugin reload, and connection limits."""

import asyncio
import time
import threading
from unittest.mock import patch, MagicMock

import pytest

from agentwork import Agent, FleetManager, Pipeline, RetryPolicy, tool
from agentwork.core.result import TaskResult, ResultStatus
from agentwork.server.app import LRUResultStore, TaskResponse, create_app
from agentwork.events import EventBus, TaskStarted
from agentwork.observability.metrics import MetricsCollector
from agentwork.persistence.sqlite_backend import SQLiteBackend
from agentwork.server.rate_limiter import RateLimiter
from agentwork.server.websocket import WebSocketManager
from agentwork.llm.prompt_template import PromptTemplate
from agentwork.plugins.plugin import Plugin
from agentwork.plugins.manifest import PluginManifest


# ============================================================================
# Original review fixes tests (LRU, parallel, jitter, auto-health, auth)
# ============================================================================


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


# ============================================================================
# New review fixes tests (v2: event bus, sqlite, rate limiter, websocket,
# metrics, prompt template, plugin reload)
# ============================================================================


class TestEventBusAsyncHandlerInRunningLoop:
    """Verify async handlers fire when publish() is called inside a running loop."""

    @pytest.mark.asyncio
    async def test_publish_schedules_async_handler_in_running_loop(self):
        """publish() schedules async handlers via loop.create_task when loop is running."""
        bus = EventBus()
        received = []

        async def async_handler(event):
            received.append(event)

        bus.subscribe("task.started", async_handler)
        bus.publish(TaskStarted(task_id="t1"))

        # Give the event loop a chance to run the created task
        await asyncio.sleep(0.05)
        assert len(received) == 1
        assert received[0].task_id == "t1"

    @pytest.mark.asyncio
    async def test_replay_schedules_async_handler_in_running_loop(self):
        """replay() schedules async handlers via loop.create_task when loop is running."""
        bus = EventBus()
        bus.publish(TaskStarted(task_id="t1"))
        bus.publish(TaskStarted(task_id="t2"))

        replayed = []

        async def async_handler(event):
            replayed.append(event)

        bus.replay("task.*", handler=async_handler)

        await asyncio.sleep(0.05)
        assert len(replayed) == 2


class TestSQLiteBackendThreadSafety:
    """Verify SQLiteBackend can be used from multiple threads safely."""

    def test_concurrent_writes(self):
        """Multiple threads can write to SQLiteBackend without errors."""
        backend = SQLiteBackend(db_path=":memory:")
        errors = []

        def writer(thread_id):
            try:
                for i in range(20):
                    backend.save_result(
                        f"task-{thread_id}-{i}", {"thread": thread_id, "i": i}
                    )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        # All 100 results should be stored
        results = backend.list_results(limit=200)
        assert len(results) == 100

    def test_concurrent_read_write(self):
        """Reading and writing from different threads works safely."""
        backend = SQLiteBackend(db_path=":memory:")
        backend.save_result("seed", {"value": "initial"})
        errors = []

        def reader():
            try:
                for _ in range(50):
                    backend.get_result("seed")
            except Exception as e:
                errors.append(e)

        def writer():
            try:
                for i in range(50):
                    backend.save_knowledge(f"key-{i}", f"value-{i}")
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=reader)
        t2 = threading.Thread(target=writer)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert errors == []


class TestRateLimiterBoundedBuckets:
    """Verify rate limiter evicts old clients when max_clients is exceeded."""

    def test_evicts_oldest_when_max_clients_exceeded(self):
        """Oldest bucket entries are evicted when max_clients is reached."""
        limiter = RateLimiter(rate=10.0, capacity=5, max_clients=3)

        limiter.allow("client-1")
        limiter.allow("client-2")
        limiter.allow("client-3")
        # All three clients tracked
        assert len(limiter._buckets) == 3

        # Adding a 4th client should evict the oldest (client-1)
        limiter.allow("client-4")
        assert len(limiter._buckets) == 3
        assert "client-1" not in limiter._buckets
        assert "client-4" in limiter._buckets

    def test_lru_ordering_preserved(self):
        """Accessing a client moves it to the end, protecting it from eviction."""
        limiter = RateLimiter(rate=10.0, capacity=5, max_clients=3)

        limiter.allow("client-1")
        limiter.allow("client-2")
        limiter.allow("client-3")

        # Access client-1 again to move it to end
        limiter.allow("client-1")

        # Adding client-4 should evict client-2 (now the oldest)
        limiter.allow("client-4")
        assert "client-1" in limiter._buckets
        assert "client-2" not in limiter._buckets

    def test_default_max_clients(self):
        """Default max_clients is 10000."""
        limiter = RateLimiter()
        assert limiter._max_clients == 10000


class TestWebSocketManagerConnectionLimit:
    """Verify WebSocket manager rejects connections when limit is reached."""

    @pytest.mark.asyncio
    async def test_rejects_when_limit_reached(self):
        """New connections are rejected when max_connections is reached."""
        manager = WebSocketManager(max_connections=2)

        class FakeWS:
            def __init__(self, name):
                self.name = name

        ws1 = FakeWS("ws1")
        ws2 = FakeWS("ws2")
        ws3 = FakeWS("ws3")

        assert await manager.connect(ws1) is True
        assert await manager.connect(ws2) is True
        # Third connection should be rejected
        assert await manager.connect(ws3) is False
        assert manager.active_connections == 2

    @pytest.mark.asyncio
    async def test_allows_after_disconnect(self):
        """After disconnecting a client, new connections are accepted."""
        manager = WebSocketManager(max_connections=2)

        class FakeWS:
            def __init__(self, name):
                self.name = name

        ws1 = FakeWS("ws1")
        ws2 = FakeWS("ws2")
        ws3 = FakeWS("ws3")

        await manager.connect(ws1)
        await manager.connect(ws2)
        assert await manager.connect(ws3) is False

        await manager.disconnect(ws1)
        assert await manager.connect(ws3) is True
        assert manager.active_connections == 2

    @pytest.mark.asyncio
    async def test_resubscription_does_not_count_as_new(self):
        """An already-connected client can subscribe to additional tasks."""
        manager = WebSocketManager(max_connections=2)

        class FakeWS:
            def __init__(self, name):
                self.name = name

        ws1 = FakeWS("ws1")
        ws2 = FakeWS("ws2")

        await manager.connect(ws1)
        await manager.connect(ws2)
        # ws1 re-subscribing to a task should succeed
        assert await manager.connect(ws1, task_id="task-123") is True
        assert manager.active_connections == 2

    @pytest.mark.asyncio
    async def test_default_max_connections(self):
        """Default max_connections is 1000."""
        manager = WebSocketManager()
        assert manager._max_connections == 1000


class TestMetricsCollectorBoundedHistogram:
    """Verify histogram values are capped at max_values."""

    def test_caps_histogram_values(self):
        """Histogram discards oldest values when max_values exceeded."""
        collector = MetricsCollector(max_values=5)

        for i in range(10):
            collector.histogram("latency", float(i))

        metrics = collector.get_metrics()
        values = metrics["histograms"]["latency"]["values"]
        assert len(values) == 5
        # Should keep the most recent values (5, 6, 7, 8, 9)
        assert values == [5.0, 6.0, 7.0, 8.0, 9.0]

    def test_default_max_values(self):
        """Default max_values is 10000."""
        collector = MetricsCollector()
        assert collector._max_values == 10000

    def test_within_limit_no_truncation(self):
        """Values within limit are not affected."""
        collector = MetricsCollector(max_values=100)
        for i in range(50):
            collector.histogram("metric", float(i))

        metrics = collector.get_metrics()
        values = metrics["histograms"]["metric"]["values"]
        assert len(values) == 50


class TestPromptTemplateInjectionPrevention:
    """Verify format-string injection is blocked."""

    def test_attribute_access_not_allowed(self):
        """Attribute access patterns like {name.__class__} are not substituted."""
        template = PromptTemplate("Hello {name.__class__}")
        # The pattern {name.__class__} does NOT match our simple variable regex
        # so it should be left as-is (no variables detected)
        assert template.variables == []
        result = template.render()
        assert "{name.__class__}" in result

    def test_nested_braces_not_interpreted(self):
        """Complex format specs are not interpreted."""
        template = PromptTemplate("Value: {val!r}")
        # !r is not a valid variable name character, so not matched
        assert template.variables == []

    def test_simple_substitution_works(self):
        """Simple {variable} substitution still works correctly."""
        template = PromptTemplate("Hello, {name}! You are a {role}.")
        result = template.render(name="Alice", role="developer")
        assert result == "Hello, Alice! You are a developer."

    def test_format_spec_not_processed(self):
        """Format specs like {value:.2f} are not processed."""
        template = PromptTemplate("Price: {value:.2f}")
        # The regex only matches simple identifiers, not format specs
        assert template.variables == []

    def test_missing_variable_raises_key_error(self):
        """Missing required variables still raise KeyError."""
        template = PromptTemplate("{greeting}, {name}!")
        with pytest.raises(KeyError):
            template.render(greeting="Hi")

    def test_object_with_dunder_attribute(self):
        """Passing an object as a value does not expose its attributes."""

        class Evil:
            secret = "should_not_see_this"

            def __str__(self):
                return "safe_string"

        template = PromptTemplate("Hello {name}")
        result = template.render(name=Evil())
        assert result == "Hello safe_string"
        assert "should_not_see_this" not in result


class TestPluginHotReload:
    """Verify plugin hot-reload properly reloads modules."""

    def test_file_path_reload_picks_up_changes(self, tmp_path):
        """File-path plugins pick up changes on reload."""
        module_path = tmp_path / "my_plugin.py"
        module_path.write_text('''
from agentwork.tools.decorators import tool

@tool(name="original", description="Original tool")
def original() -> str:
    return "original"
''')

        manifest = PluginManifest(name="test-plugin", entry_point=str(module_path))
        plugin = Plugin(manifest)
        plugin.load()
        assert len(plugin.tools) == 1
        assert plugin.tools[0].name == "original"

        # Modify the module
        module_path.write_text('''
from agentwork.tools.decorators import tool

@tool(name="updated", description="Updated tool")
def updated() -> str:
    return "updated"
''')

        plugin.reload()
        assert plugin.loaded is True
        assert len(plugin.tools) == 1
        assert plugin.tools[0].name == "updated"

    def test_reload_stores_module_reference(self, tmp_path):
        """Plugin stores module reference after load."""
        module_path = tmp_path / "my_plugin.py"
        module_path.write_text('''
from agentwork.tools.decorators import tool

@tool(name="test_tool", description="Test")
def test_tool() -> str:
    return "test"
''')

        manifest = PluginManifest(name="ref-plugin", entry_point=str(module_path))
        plugin = Plugin(manifest)
        plugin.load()
        assert plugin._module is not None

    def test_unload_clears_module_reference(self, tmp_path):
        """Plugin clears module reference after unload."""
        module_path = tmp_path / "my_plugin.py"
        module_path.write_text('''
from agentwork.tools.decorators import tool

@tool(name="test_tool", description="Test")
def test_tool() -> str:
    return "test"
''')

        manifest = PluginManifest(name="clear-plugin", entry_point=str(module_path))
        plugin = Plugin(manifest)
        plugin.load()
        assert plugin._module is not None
        plugin.unload()
        assert plugin._module is None
