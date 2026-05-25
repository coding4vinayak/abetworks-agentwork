"""AgentWork - Production-grade agent framework with retry, scheduling, and fleet management."""

from agentwork.core.agent import Agent, BaseAgent
from agentwork.core.result import TaskResult
from agentwork.core.context import ExecutionContext
from agentwork.core.exceptions import (
    AgentError,
    ToolError,
    RetryableError,
    FatalError,
    TimeoutError as AgentTimeoutError,
)
from agentwork.tools.base import Tool
from agentwork.tools.decorators import tool
from agentwork.tools.registry import ToolRegistry
from agentwork.resilience.retry import RetryPolicy
from agentwork.resilience.fallback import FallbackChain
from agentwork.resilience.circuit_breaker import CircuitBreaker
from agentwork.resilience.timeout import Timeout
from agentwork.engine.pipeline import Pipeline
from agentwork.engine.planner import TaskPlanner
from agentwork.engine.executor import TaskExecutor
from agentwork.scheduler.scheduler import Scheduler
from agentwork.scheduler.worker import Worker
from agentwork.scheduler.triggers import CronTrigger, IntervalTrigger, OnceTrigger
from agentwork.fleet.manager import FleetManager
from agentwork.fleet.router import TaskRouter
from agentwork.fleet.pool import AgentPool

__version__ = "2.0.0"

__all__ = [
    "Agent",
    "BaseAgent",
    "TaskResult",
    "ExecutionContext",
    "AgentError",
    "ToolError",
    "RetryableError",
    "FatalError",
    "AgentTimeoutError",
    "Tool",
    "tool",
    "ToolRegistry",
    "RetryPolicy",
    "FallbackChain",
    "CircuitBreaker",
    "Timeout",
    "Pipeline",
    "TaskPlanner",
    "TaskExecutor",
    "Scheduler",
    "Worker",
    "CronTrigger",
    "IntervalTrigger",
    "OnceTrigger",
    "FleetManager",
    "TaskRouter",
    "AgentPool",
]
