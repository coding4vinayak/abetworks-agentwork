"""Factory function to create an LLM tool from a provider."""

from __future__ import annotations

from agentwork.llm.providers import LLMProvider
from agentwork.tools.base import Tool


def create_llm_tool(
    provider: LLMProvider,
    name: str = "llm",
    description: str = "Generate LLM response",
) -> Tool:
    """Create a Tool instance that uses an LLM provider to generate responses.

    The resulting tool takes a prompt (str) and returns the LLM response content.
    It can be added to an Agent and executed like any other tool.

    Usage:
        provider = OpenAIProvider(api_key="...")
        llm_tool = create_llm_tool(provider)
        agent = Agent(name="MyAgent", tools=[llm_tool])
        result = agent.execute("llm", {"prompt": "Hello!"})
    """

    def llm_function(prompt: str) -> str:
        response = provider.complete(prompt)
        return response.content

    return Tool(
        name=name,
        description=description,
        function=llm_function,
    )
