"""Tests for the tool system."""

import pytest

from agentwork import tool, Tool
from agentwork.tools.registry import ToolRegistry
from agentwork.core.result import ResultStatus


class TestToolDecorator:
    def test_basic_tool(self):
        @tool(name="hello", description="Says hello")
        def hello(name: str) -> str:
            return f"Hello, {name}!"

        assert isinstance(hello, Tool)
        assert hello.name == "hello"
        assert hello.description == "Says hello"

    def test_tool_execute(self):
        @tool(name="add", description="Adds numbers")
        def add(a: int, b: int) -> int:
            return a + b

        result = add.execute(a=2, b=3)
        assert result.success
        assert result.output == 5

    def test_tool_with_fallback(self):
        @tool(name="risky", description="Risky op", fallback=lambda: "safe")
        def risky() -> str:
            raise ValueError("oops")

        result = risky.execute()
        assert result.success
        assert result.output == "safe"
        assert result.metadata.get("used_fallback") is True

    def test_tool_with_retry(self):
        call_count = {"n": 0}

        @tool(name="flaky", description="Flaky tool", retry_attempts=3)
        def flaky() -> str:
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise ValueError("not yet")
            return "done"

        result = flaky.execute()
        assert result.success
        assert result.output == "done"

    def test_tool_failure_no_crash(self):
        @tool(name="crash", description="Always crashes")
        def crash() -> str:
            raise RuntimeError("boom")

        result = crash.execute()
        assert result.failed
        assert "boom" in result.error

    def test_tool_infers_name(self):
        @tool(description="Auto named")
        def my_function() -> str:
            return "ok"

        assert my_function.name == "my_function"


class TestToolRegistry:
    def test_register_and_get(self):
        @tool(name="t1", description="Tool 1")
        def t1() -> str:
            return "t1"

        registry = ToolRegistry()
        registry.register(t1)
        assert registry.get("t1") is t1
        assert registry.has("t1")
        assert "t1" in registry

    def test_unregister(self):
        @tool(name="t1", description="Tool 1")
        def t1() -> str:
            return "t1"

        registry = ToolRegistry()
        registry.register(t1)
        removed = registry.unregister("t1")
        assert removed is t1
        assert not registry.has("t1")

    def test_get_by_tag(self):
        @tool(name="web", description="Web tool", tags=["http", "network"])
        def web() -> str:
            return "web"

        @tool(name="db", description="DB tool", tags=["database"])
        def db() -> str:
            return "db"

        registry = ToolRegistry()
        registry.register(web)
        registry.register(db)

        http_tools = registry.get_by_tag("http")
        assert len(http_tools) == 1
        assert http_tools[0].name == "web"

    def test_list_tools(self):
        registry = ToolRegistry()

        @tool(name="a", description="A")
        def a() -> str:
            return "a"

        @tool(name="b", description="B")
        def b() -> str:
            return "b"

        registry.register(a)
        registry.register(b)
        assert len(registry.list_tools()) == 2
        assert len(registry) == 2

    def test_clear(self):
        @tool(name="t", description="T")
        def t() -> str:
            return "t"

        registry = ToolRegistry()
        registry.register(t)
        registry.clear()
        assert len(registry) == 0
