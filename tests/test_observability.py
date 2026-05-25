"""Tests for the observability module."""

import json
import time
from unittest.mock import patch

import pytest

from agentwork.observability.logger import StructuredLogger
from agentwork.observability.metrics import MetricsCollector, timed
from agentwork.observability.tracing import TraceContext, current_trace
from agentwork.observability.exporters import (
    ConsoleExporter,
    FileExporter,
    OTELExporter,
    Exporter,
)
from agentwork.observability.decorators import instrument


class TestStructuredLogger:
    """Test StructuredLogger JSON output."""

    def test_info_outputs_json(self, capsys):
        """info() outputs valid JSON."""
        logger = StructuredLogger.get_logger("test_info")
        logger.info("hello world")
        captured = capsys.readouterr()
        data = json.loads(captured.err.strip())
        assert data["level"] == "INFO"
        assert data["message"] == "hello world"
        assert data["logger"] == "test_info"

    def test_warning_outputs_json(self, capsys):
        """warning() outputs valid JSON with WARNING level."""
        logger = StructuredLogger.get_logger("test_warning")
        logger.warning("watch out")
        captured = capsys.readouterr()
        data = json.loads(captured.err.strip())
        assert data["level"] == "WARNING"
        assert data["message"] == "watch out"

    def test_error_outputs_json(self, capsys):
        """error() outputs valid JSON with ERROR level."""
        logger = StructuredLogger.get_logger("test_error")
        logger.error("something broke")
        captured = capsys.readouterr()
        data = json.loads(captured.err.strip())
        assert data["level"] == "ERROR"

    def test_extra_fields_included(self, capsys):
        """Extra kwargs are included in the JSON output."""
        logger = StructuredLogger.get_logger("test_extra")
        logger.info("event", user_id="abc", count=5)
        captured = capsys.readouterr()
        data = json.loads(captured.err.strip())
        assert data["user_id"] == "abc"
        assert data["count"] == 5

    def test_trace_context_included(self, capsys):
        """Logger includes trace_id and span_id from active TraceContext."""
        logger = StructuredLogger.get_logger("test_trace")
        with TraceContext() as ctx:
            logger.info("traced message")
        captured = capsys.readouterr()
        data = json.loads(captured.err.strip())
        assert data["trace_id"] == ctx.trace_id
        assert data["span_id"] == ctx.span_id

    def test_no_trace_context_sets_none(self, capsys):
        """Without active trace, trace_id and span_id are None."""
        logger = StructuredLogger.get_logger("test_no_trace")
        logger.info("no trace")
        captured = capsys.readouterr()
        data = json.loads(captured.err.strip())
        assert data["trace_id"] is None
        assert data["span_id"] is None


class TestMetricsCollector:
    """Test MetricsCollector counter/gauge/histogram."""

    @pytest.fixture
    def collector(self):
        return MetricsCollector()

    def test_counter_increments(self, collector):
        """counter() increments the named counter."""
        collector.counter("requests")
        collector.counter("requests")
        metrics = collector.get_metrics()
        assert metrics["counters"]["requests"]["value"] == 2

    def test_counter_with_value(self, collector):
        """counter() can increment by a specified value."""
        collector.counter("bytes", value=100)
        collector.counter("bytes", value=50)
        metrics = collector.get_metrics()
        assert metrics["counters"]["bytes"]["value"] == 150

    def test_gauge_sets_value(self, collector):
        """gauge() sets the metric to the specified value."""
        collector.gauge("temperature", 72.5)
        metrics = collector.get_metrics()
        assert metrics["gauges"]["temperature"]["value"] == 72.5

    def test_gauge_overwrites(self, collector):
        """gauge() overwrites previous value."""
        collector.gauge("cpu", 50.0)
        collector.gauge("cpu", 75.0)
        metrics = collector.get_metrics()
        assert metrics["gauges"]["cpu"]["value"] == 75.0

    def test_histogram_records_values(self, collector):
        """histogram() appends values to the list."""
        collector.histogram("latency", 1.5)
        collector.histogram("latency", 2.0)
        collector.histogram("latency", 0.8)
        metrics = collector.get_metrics()
        assert metrics["histograms"]["latency"]["values"] == [1.5, 2.0, 0.8]

    def test_reset_clears_all(self, collector):
        """reset() clears all metrics."""
        collector.counter("a")
        collector.gauge("b", 1.0)
        collector.histogram("c", 1.0)
        collector.reset()
        metrics = collector.get_metrics()
        assert metrics["counters"] == {}
        assert metrics["gauges"] == {}
        assert metrics["histograms"] == {}

    def test_tags_create_separate_entries(self, collector):
        """Different tags create separate metric entries."""
        collector.counter("requests", tags={"method": "GET"})
        collector.counter("requests", tags={"method": "POST"})
        metrics = collector.get_metrics()
        assert len(metrics["counters"]) == 2


class TestTimedDecorator:
    """Test the @timed decorator."""

    def test_timed_records_duration(self):
        """@timed records execution time as histogram."""
        collector = MetricsCollector()

        @timed("func.duration", collector)
        def slow_func():
            time.sleep(0.01)
            return "done"

        result = slow_func()
        assert result == "done"
        metrics = collector.get_metrics()
        values = metrics["histograms"]["func.duration"]["values"]
        assert len(values) == 1
        assert values[0] >= 0.01


class TestTraceContext:
    """Test TraceContext ID generation and context propagation."""

    def test_generates_trace_id(self):
        """TraceContext auto-generates a trace_id."""
        ctx = TraceContext()
        assert ctx.trace_id is not None
        assert len(ctx.trace_id) > 0

    def test_generates_span_id(self):
        """TraceContext auto-generates a span_id."""
        ctx = TraceContext()
        assert ctx.span_id is not None
        assert ctx.span_id != ctx.trace_id

    def test_parent_span_id_optional(self):
        """parent_span_id defaults to None."""
        ctx = TraceContext()
        assert ctx.parent_span_id is None

    def test_context_manager_sets_current(self):
        """Using TraceContext as context manager sets current_trace()."""
        with TraceContext() as ctx:
            assert current_trace() is ctx

    def test_context_manager_restores_previous(self):
        """Exiting context manager restores previous trace."""
        assert current_trace() is None
        with TraceContext():
            pass
        assert current_trace() is None

    def test_nested_contexts(self):
        """Nested TraceContext correctly sets and restores."""
        with TraceContext() as outer:
            assert current_trace() is outer
            with TraceContext() as inner:
                assert current_trace() is inner
            assert current_trace() is outer
        assert current_trace() is None

    def test_current_trace_returns_none_outside_context(self):
        """current_trace() returns None when no context is active."""
        assert current_trace() is None


class TestInstrumentDecorator:
    """Test the @instrument decorator."""

    def test_instrument_creates_span(self):
        """@instrument creates a TraceContext span during execution."""
        seen_traces = []

        @instrument(name="test_span")
        def my_func():
            seen_traces.append(current_trace())
            return 42

        result = my_func()
        assert result == 42
        assert len(seen_traces) == 1
        assert seen_traces[0] is not None
        assert seen_traces[0].trace_id is not None

    def test_instrument_records_duration(self):
        """@instrument records duration when collector provided."""
        collector = MetricsCollector()

        @instrument(name="timed_op", collector=collector)
        def my_func():
            time.sleep(0.01)

        my_func()
        metrics = collector.get_metrics()
        values = metrics["histograms"]["timed_op.duration"]["values"]
        assert len(values) == 1
        assert values[0] >= 0.01

    def test_instrument_reraises_exceptions(self):
        """@instrument re-raises exceptions."""

        @instrument(name="failing")
        def my_func():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            my_func()

    @pytest.mark.asyncio
    async def test_instrument_async(self):
        """@instrument works with async functions."""
        collector = MetricsCollector()

        @instrument(name="async_op", collector=collector)
        async def my_async():
            return "async_result"

        result = await my_async()
        assert result == "async_result"
        metrics = collector.get_metrics()
        assert "async_op.duration" in metrics["histograms"]


class TestExporters:
    """Test exporter implementations."""

    def test_exporter_is_abstract(self):
        """Exporter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Exporter()

    def test_console_exporter(self, capsys):
        """ConsoleExporter prints JSON to stdout."""
        exporter = ConsoleExporter()
        exporter.export([{"key": "value"}])
        captured = capsys.readouterr()
        data = json.loads(captured.out.strip())
        assert data == {"key": "value"}

    def test_file_exporter(self, tmp_path):
        """FileExporter writes JSON lines to a file."""
        file_path = str(tmp_path / "metrics.jsonl")
        exporter = FileExporter(file_path)
        exporter.export([{"a": 1}, {"b": 2}])

        with open(file_path) as f:
            lines = f.readlines()
        assert len(lines) == 2
        assert json.loads(lines[0]) == {"a": 1}
        assert json.loads(lines[1]) == {"b": 2}

    def test_otel_exporter(self, capsys):
        """OTELExporter outputs OTEL-compatible JSON structure."""
        exporter = OTELExporter()
        exporter.export([{"span": "test"}])
        captured = capsys.readouterr()
        data = json.loads(captured.out.strip())
        assert "resourceSpans" in data
        spans = data["resourceSpans"][0]["scopeSpans"][0]["spans"]
        assert spans == [{"span": "test"}]
