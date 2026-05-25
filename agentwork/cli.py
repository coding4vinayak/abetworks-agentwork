"""Command-line interface for AgentWork framework."""

from __future__ import annotations

import argparse
import sys
from typing import List


def main(argv: List[str] | None = None) -> None:
    """Entry point for the agentwork CLI."""
    parser = argparse.ArgumentParser(
        prog="agentwork",
        description="AgentWork - Production-grade agent framework CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    # run subcommand
    run_parser = subparsers.add_parser("run", help="Run a task with a company type")
    run_parser.add_argument("company_type", help="Company type to use")
    run_parser.add_argument("task", help="Task description to execute")

    # list-companies subcommand
    subparsers.add_parser("list-companies", help="List available company types")

    # list-tools subcommand
    tools_parser = subparsers.add_parser(
        "list-tools", help="List tools for a company type"
    )
    tools_parser.add_argument("company_type", help="Company type to inspect")

    # serve subcommand
    serve_parser = subparsers.add_parser(
        "serve", help="Start HTTP server for a company type"
    )
    serve_parser.add_argument("company_type", help="Company type to serve")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return

    if args.command == "list-companies":
        _list_companies()
    elif args.command == "list-tools":
        _list_tools(args.company_type)
    elif args.command == "run":
        _run_task(args.company_type, args.task)
    elif args.command == "serve":
        _serve(args.company_type, args.host, args.port)


def _list_companies() -> None:
    """Print all available company types."""
    from agentwork.factory import TeamFactory

    for name in sorted(TeamFactory.COMPANY_FACTORIES.keys()):
        print(name)


def _list_tools(company_type: str) -> None:
    """Print all tool names for a given company type."""
    from agentwork.factory import TeamFactory

    if company_type not in TeamFactory.COMPANY_FACTORIES:
        print(f"Error: Unknown company type '{company_type}'", file=sys.stderr)
        print(
            f"Available types: {', '.join(sorted(TeamFactory.COMPANY_FACTORIES.keys()))}",
            file=sys.stderr,
        )
        sys.exit(1)

    factory_func = TeamFactory.COMPANY_FACTORIES[company_type]
    agents = factory_func()

    tool_names: list[str] = []
    for agent in agents:
        for tool in agent.tools:
            tool_names.append(tool.name)

    for name in sorted(set(tool_names)):
        print(name)


def _run_task(company_type: str, task: str) -> None:
    """Create a company orchestrator and run a demo task."""
    from agentwork.factory import TeamFactory
    from agentwork.orchestrator import CompanyOrchestrator

    if company_type not in TeamFactory.COMPANY_FACTORIES:
        print(f"Error: Unknown company type '{company_type}'", file=sys.stderr)
        print(
            f"Available types: {', '.join(sorted(TeamFactory.COMPANY_FACTORIES.keys()))}",
            file=sys.stderr,
        )
        sys.exit(1)

    factory_func = TeamFactory.COMPANY_FACTORIES[company_type]
    agents = factory_func()
    orchestrator = CompanyOrchestrator(agents=agents)

    # Create a simple sub-task using the first available tool
    if agents and agents[0].tools:
        first_tool = agents[0].tools[0]
        result = orchestrator.orchestrate(
            task_description=task,
            sub_tasks=[{"name": first_tool.name, "input_data": {}, "depends_on": []}],
        )
        print(f"Task ID: {result.task_id}")
        print(f"Status: {result.status}")
        print(f"Duration: {result.duration_ms:.1f}ms")
        print(f"Output: {result.final_output}")
    else:
        print("No tools available for this company type.")


def _serve(company_type: str, host: str, port: int) -> None:
    """Start HTTP server for a company type."""
    from agentwork.factory import TeamFactory
    from agentwork.orchestrator import CompanyOrchestrator
    from agentwork.server.fleet_app import create_fleet_app

    if company_type not in TeamFactory.COMPANY_FACTORIES:
        print(f"Error: Unknown company type '{company_type}'", file=sys.stderr)
        print(
            f"Available types: {', '.join(sorted(TeamFactory.COMPANY_FACTORIES.keys()))}",
            file=sys.stderr,
        )
        sys.exit(1)

    factory_func = TeamFactory.COMPANY_FACTORIES[company_type]
    agents = factory_func()
    orchestrator = CompanyOrchestrator(agents=agents)
    app = create_fleet_app(orchestrator)

    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
