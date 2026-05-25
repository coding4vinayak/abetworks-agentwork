# AgentWork

Production-grade agent framework with retry, scheduling, fleet management, and remote API access.

## Installation

```bash
pip install abetworks-agentwork
```

For HTTP server support:
```bash
pip install abetworks-agentwork[server]
```

## Quick Start

```python
from agentwork import Agent, tool

@tool(name="greet", description="Greets a person", retry_attempts=3)
def greet(name: str) -> str:
    return f"Hello, {name}!"

@tool(name="process", description="Processes data", retry_attempts=5, fallback=lambda data: {"result": "default"})
def process(data: dict) -> dict:
    return {"result": data}

agent = Agent(name="MyAgent", tools=[greet, process])
result = agent.execute("greet", {"name": "World"})
print(result.status)   # "success"
print(result.output)   # "Hello, World!"
```

## Features

### Tools with Retry and Fallback

Every tool execution is wrapped with configurable retry logic and fallback strategies. If all retries are exhausted, the framework returns a partial result with error info rather than crashing.

```python
from agentwork import tool, RetryPolicy, FallbackChain

@tool(
    name="fetch_data",
    description="Fetches data from external source",
    retry_attempts=5,
    fallback=lambda source: {"data": [], "cached": True}
)
def fetch_data(source: str) -> dict:
    # Your data fetching logic
    return {"data": [...], "cached": False}
```

### Pipeline (Sequential and Parallel Execution)

```python
from agentwork import Pipeline, tool

@tool(name="step_1", description="First step")
def step_1(data: str) -> dict:
    return {"processed": data.upper()}

@tool(name="step_2", description="Second step")
def step_2(processed: str) -> str:
    return f"Result: {processed}"

pipeline = Pipeline(tools=[step_1, step_2])
result = pipeline.run({"data": "hello"})
print(result.output)  # "Result: HELLO"

# Parallel execution
result = pipeline.run_parallel({"data": "hello"})
```

### Scheduling

```python
from agentwork import Scheduler, Worker
from agentwork.scheduler.triggers import IntervalTrigger, CronTrigger

scheduler = Scheduler()
scheduler.add_job(my_cleanup_func, IntervalTrigger(minutes=30))
scheduler.add_job(my_report_func, CronTrigger("0 9 * * MON"))  # Every Monday 9 AM

worker = Worker(scheduler)
worker.start()  # Blocking - runs scheduled jobs
```

### Fleet Management

```python
from agentwork import Agent, FleetManager, tool

@tool(name="send_email", description="Sends email")
def send_email(to: str, body: str) -> dict:
    return {"sent": True}

@tool(name="generate_report", description="Generates report")
def generate_report(type: str) -> dict:
    return {"report": f"{type} report"}

email_agent = Agent(name="EmailAgent", tools=[send_email])
report_agent = Agent(name="ReportAgent", tools=[generate_report])

fleet = FleetManager()
fleet.register(email_agent)
fleet.register(report_agent)

# Automatically routes to the right agent
result = fleet.dispatch("send_email", {"to": "user@example.com", "body": "Hi!"})
```

### Domain Presets

```python
from agentwork.presets import OfficeAgent, MarketingAgent, SalesAgent, DigitalAgent, EntertainmentAgent

# Pre-configured agents with relevant tools
office = OfficeAgent()
marketing = MarketingAgent()
sales = SalesAgent()
digital = DigitalAgent()
entertainment = EntertainmentAgent()

# Execute pre-loaded tools
result = office.execute("document_processor", {"content": "Report text", "format": "pdf"})
```

### Remote API / HTTP Server

Expose any agent over HTTP with task ID tracking. Multiple tasks run concurrently, each with a unique ID. Results are stored and retrievable by task_id so responses go back to the correct requester.

```python
from agentwork import Agent, tool
from agentwork.server import create_app

@tool(name="analyze", description="Analyze data")
def analyze(data: dict) -> dict:
    return {"analysis": "complete", "score": 95}

agent = Agent(name="AnalyzerAgent", tools=[analyze])
app = create_app(agent)

# Run with: uvicorn myapp:app --host 0.0.0.0 --port 8000
```

**API Endpoints:**
- `POST /execute` - Submit a task (with optional client-specified `task_id`)
- `GET /result/{task_id}` - Retrieve result by task_id
- `GET /tools` - List available tools
- `GET /health` - Health check

**Example remote usage:**
```bash
# Submit a task with your own ID for tracking
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"task_id": "my-request-123", "tool": "analyze", "input": {"data": {"value": 42}}}'

# Later, retrieve the result by ID
curl http://localhost:8000/result/my-request-123
```

### Resilience Patterns

```python
from agentwork import RetryPolicy, FallbackChain, CircuitBreaker, Timeout

# Retry with exponential backoff
policy = RetryPolicy(max_attempts=5, backoff_base=1.0, jitter=0.5)
result = policy.execute(my_function, arg1, arg2)

# Fallback chain
chain = FallbackChain(strategies=[primary_func, secondary_func, cache_func])
result = chain.execute(data)

# Circuit breaker
breaker = CircuitBreaker(failure_threshold=5, cooldown_seconds=30)
result = breaker.execute(external_api_call)

# Timeout
timeout = Timeout(seconds=10.0)
result = timeout.execute(slow_function)
```

## Design Principles

- **Never fail**: Every tool execution has retry + fallback. Returns partial results rather than crashing.
- **Composable**: Tools are simple decorated functions. Agents are composed of tools.
- **Observable**: Logs every execution step, retry attempt, and fallback activation.
- **Type-safe**: Uses pydantic models and type hints throughout.
- **Simple API**: Creating an agent is 3-5 lines of code.
- **Remote-ready**: Expose any agent over HTTP with task ID tracking for concurrent access.

## License

MIT
