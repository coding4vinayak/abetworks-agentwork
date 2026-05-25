"""Developer agent preset with coding, debugging, and testing tools."""

from __future__ import annotations

from typing import Any, Dict

from agentwork.core.agent import Agent
from agentwork.tools.decorators import tool


@tool(name="code_generator", description="Generate code from specifications", retry_attempts=3)
def code_generator(spec: str = "", language: str = "python") -> Dict[str, Any]:
    """Generate code from specs. Override with your code generation logic."""
    return {"spec": spec, "language": language, "code": "generated", "lines": 0}


@tool(name="bug_fixer", description="Diagnose and fix bugs in code", retry_attempts=3)
def bug_fixer(bug_report: str = "", code: str = "") -> Dict[str, Any]:
    """Fix bugs in code. Override with your bug fixing logic."""
    return {"bug_report": bug_report, "fixed": True, "changes": 1}


@tool(name="test_writer", description="Write automated tests for code", retry_attempts=2)
def test_writer(code: str = "", framework: str = "pytest") -> Dict[str, Any]:
    """Write tests for code. Override with your test generation logic."""
    return {"framework": framework, "tests_written": 1, "coverage": "basic"}


@tool(name="code_refactorer", description="Refactor code for better quality and maintainability", retry_attempts=2)
def code_refactorer(code: str = "", goal: str = "readability") -> Dict[str, Any]:
    """Refactor code. Override with your refactoring logic."""
    return {"goal": goal, "refactored": True, "improvements": 1}


def DeveloperAgent(name: str = "DeveloperAgent", **kwargs: Any) -> Agent:
    """Create a developer agent pre-configured with software development tools.

    Tools included:
    - code_generator: Generate code from specifications
    - bug_fixer: Diagnose and fix bugs in code
    - test_writer: Write automated tests for code
    - code_refactorer: Refactor code for better quality and maintainability
    """
    return Agent(
        name=name,
        description="Software development agent for coding, testing, debugging, and refactoring",
        tools=[code_generator, bug_fixer, test_writer, code_refactorer],
        capabilities=["coding", "testing", "debugging", "development"],
        **kwargs,
    )
