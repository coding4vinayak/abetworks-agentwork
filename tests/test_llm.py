"""Comprehensive tests for the LLM integration module."""

import pytest

from agentwork import (
    Agent,
    LLMProvider,
    LLMResponse,
    TokenUsage,
    OpenAIProvider,
    AnthropicProvider,
    PromptTemplate,
    TokenCounter,
    create_llm_tool,
)
from agentwork.llm.providers import LLMProvider as DirectLLMProvider


class TestLLMProvider:
    """Tests for the abstract LLMProvider base class."""

    def test_cannot_instantiate_abc(self):
        """LLMProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMProvider()

    def test_is_abstract(self):
        """LLMProvider defines abstract methods."""
        assert hasattr(LLMProvider, "complete")
        assert hasattr(LLMProvider, "complete_async")
        assert hasattr(LLMProvider, "stream")
        assert hasattr(LLMProvider, "get_token_count")

    def test_incomplete_subclass_raises(self):
        """Subclass missing methods cannot be instantiated."""

        class IncompleteProvider(LLMProvider):
            pass

        with pytest.raises(TypeError):
            IncompleteProvider()


class TestTokenUsage:
    """Tests for the TokenUsage model."""

    def test_defaults(self):
        """TokenUsage has zero defaults."""
        usage = TokenUsage()
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0

    def test_custom_values(self):
        """TokenUsage accepts custom values."""
        usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 20
        assert usage.total_tokens == 30


class TestLLMResponse:
    """Tests for the LLMResponse model."""

    def test_defaults(self):
        """LLMResponse has sensible defaults."""
        response = LLMResponse()
        assert response.content == ""
        assert response.model == ""
        assert response.cost == 0.0
        assert response.metadata == {}
        assert isinstance(response.usage, TokenUsage)

    def test_custom_values(self):
        """LLMResponse accepts custom values."""
        usage = TokenUsage(prompt_tokens=5, completion_tokens=10, total_tokens=15)
        response = LLMResponse(
            content="Hello",
            model="gpt-4",
            usage=usage,
            cost=0.01,
            metadata={"key": "value"},
        )
        assert response.content == "Hello"
        assert response.model == "gpt-4"
        assert response.usage.total_tokens == 15
        assert response.cost == 0.01
        assert response.metadata == {"key": "value"}


class TestOpenAIProvider:
    """Tests for the OpenAI provider."""

    def test_init_defaults(self):
        """OpenAIProvider initializes with defaults."""
        provider = OpenAIProvider()
        assert provider.api_key == ""
        assert provider.base_url == "https://api.openai.com/v1"
        assert provider.model == "gpt-4"

    def test_init_custom(self):
        """OpenAIProvider accepts custom configuration."""
        provider = OpenAIProvider(
            api_key="test-key",
            base_url="http://localhost:8080",
            model="gpt-3.5-turbo",
        )
        assert provider.api_key == "test-key"
        assert provider.base_url == "http://localhost:8080"
        assert provider.model == "gpt-3.5-turbo"

    def test_complete_returns_llm_response(self):
        """complete() returns an LLMResponse with content."""
        provider = OpenAIProvider()
        response = provider.complete("Hello, world!")
        assert isinstance(response, LLMResponse)
        assert "OpenAI stub response" in response.content
        assert "Hello, world!" in response.content
        assert response.model == "gpt-4"

    def test_complete_token_usage(self):
        """complete() populates token usage."""
        provider = OpenAIProvider()
        response = provider.complete("test prompt")
        assert response.usage.prompt_tokens > 0
        assert response.usage.completion_tokens > 0
        assert response.usage.total_tokens == (
            response.usage.prompt_tokens + response.usage.completion_tokens
        )

    @pytest.mark.asyncio
    async def test_complete_async(self):
        """complete_async() returns an LLMResponse."""
        provider = OpenAIProvider()
        response = await provider.complete_async("async test")
        assert isinstance(response, LLMResponse)
        assert "OpenAI stub response" in response.content

    @pytest.mark.asyncio
    async def test_stream_yields_strings(self):
        """stream() yields string chunks."""
        provider = OpenAIProvider()
        chunks = []
        async for chunk in provider.stream("stream test"):
            chunks.append(chunk)
            assert isinstance(chunk, str)
        assert len(chunks) == 4
        assert "OpenAI stream chunk 1" in chunks[0]

    def test_get_token_count_returns_int(self):
        """get_token_count() returns a positive integer."""
        provider = OpenAIProvider()
        count = provider.get_token_count("hello world this is a test")
        assert isinstance(count, int)
        assert count > 0

    def test_get_token_count_empty_string(self):
        """get_token_count() handles empty string."""
        provider = OpenAIProvider()
        count = provider.get_token_count("")
        assert count == 0

    def test_is_llm_provider(self):
        """OpenAIProvider is an instance of LLMProvider."""
        provider = OpenAIProvider()
        assert isinstance(provider, LLMProvider)


class TestAnthropicProvider:
    """Tests for the Anthropic provider."""

    def test_init_defaults(self):
        """AnthropicProvider initializes with defaults."""
        provider = AnthropicProvider()
        assert provider.api_key == ""
        assert provider.model == "claude-3-sonnet-20240229"

    def test_init_custom(self):
        """AnthropicProvider accepts custom configuration."""
        provider = AnthropicProvider(api_key="test-key", model="claude-3-opus")
        assert provider.api_key == "test-key"
        assert provider.model == "claude-3-opus"

    def test_complete_returns_llm_response(self):
        """complete() returns an LLMResponse with content."""
        provider = AnthropicProvider()
        response = provider.complete("Hello, world!")
        assert isinstance(response, LLMResponse)
        assert "Anthropic stub response" in response.content
        assert "Hello, world!" in response.content
        assert response.model == "claude-3-sonnet-20240229"

    def test_complete_token_usage(self):
        """complete() populates token usage."""
        provider = AnthropicProvider()
        response = provider.complete("test prompt")
        assert response.usage.prompt_tokens > 0
        assert response.usage.completion_tokens > 0
        assert response.usage.total_tokens > 0

    @pytest.mark.asyncio
    async def test_complete_async(self):
        """complete_async() returns an LLMResponse."""
        provider = AnthropicProvider()
        response = await provider.complete_async("async test")
        assert isinstance(response, LLMResponse)
        assert "Anthropic stub response" in response.content

    @pytest.mark.asyncio
    async def test_stream_yields_strings(self):
        """stream() yields string chunks."""
        provider = AnthropicProvider()
        chunks = []
        async for chunk in provider.stream("stream test"):
            chunks.append(chunk)
            assert isinstance(chunk, str)
        assert len(chunks) == 4
        assert "Anthropic stream chunk 1" in chunks[0]

    def test_is_llm_provider(self):
        """AnthropicProvider is an instance of LLMProvider."""
        provider = AnthropicProvider()
        assert isinstance(provider, LLMProvider)


class TestPromptTemplate:
    """Tests for the PromptTemplate class."""

    def test_render_substitutes_variables(self):
        """render() substitutes variables correctly."""
        template = PromptTemplate("Hello, {name}! You are a {role}.")
        result = template.render(name="Alice", role="developer")
        assert result == "Hello, Alice! You are a developer."

    def test_render_single_variable(self):
        """render() works with a single variable."""
        template = PromptTemplate("Say hi to {name}")
        result = template.render(name="Bob")
        assert result == "Say hi to Bob"

    def test_render_no_variables(self):
        """render() works with no variables."""
        template = PromptTemplate("Static prompt with no vars")
        result = template.render()
        assert result == "Static prompt with no vars"

    def test_render_missing_variable_raises(self):
        """render() raises KeyError for missing required variables."""
        template = PromptTemplate("Hello, {name}! Your role is {role}.")
        with pytest.raises(KeyError):
            template.render(name="Alice")

    def test_variables_extracts_names(self):
        """variables property extracts variable names from template."""
        template = PromptTemplate("Hello, {name}! You are a {role} at {company}.")
        assert template.variables == ["name", "role", "company"]

    def test_variables_empty_template(self):
        """variables returns empty list for template without variables."""
        template = PromptTemplate("No variables here.")
        assert template.variables == []

    def test_variables_no_duplicates(self):
        """variables does not return duplicates."""
        template = PromptTemplate("{name} and {name} and {other}")
        assert template.variables == ["name", "other"]

    def test_template_stored(self):
        """Template string is stored correctly."""
        text = "My template: {var}"
        template = PromptTemplate(text)
        assert template.template == text


class TestTokenCounter:
    """Tests for the TokenCounter class."""

    def test_estimate_tokens_returns_int(self):
        """estimate_tokens() returns a positive integer."""
        counter = TokenCounter()
        result = counter.estimate_tokens("hello world this is a test")
        assert isinstance(result, int)
        assert result > 0

    def test_estimate_tokens_empty(self):
        """estimate_tokens() handles empty string."""
        counter = TokenCounter()
        result = counter.estimate_tokens("")
        assert isinstance(result, int)
        assert result >= 0

    def test_estimate_tokens_longer_text(self):
        """More text produces more tokens."""
        counter = TokenCounter()
        short = counter.estimate_tokens("hello")
        long = counter.estimate_tokens("hello world this is a much longer piece of text")
        assert long > short

    def test_estimate_cost_known_model(self):
        """estimate_cost() returns a float for known models."""
        counter = TokenCounter()
        cost = counter.estimate_cost(1000, 500, model="gpt-4")
        assert isinstance(cost, float)
        assert cost > 0
        # gpt-4: $0.03/1k prompt + $0.06/1k completion
        expected = (1000 / 1000.0) * 0.03 + (500 / 1000.0) * 0.06
        assert abs(cost - expected) < 1e-10

    def test_estimate_cost_unknown_model(self):
        """estimate_cost() returns 0.0 for unknown models."""
        counter = TokenCounter()
        cost = counter.estimate_cost(1000, 500, model="unknown-model")
        assert cost == 0.0

    def test_price_table_has_models(self):
        """PRICE_TABLE contains expected models."""
        assert "gpt-4" in TokenCounter.PRICE_TABLE
        assert "gpt-3.5-turbo" in TokenCounter.PRICE_TABLE
        assert "claude-3-sonnet" in TokenCounter.PRICE_TABLE
        assert "claude-3-opus" in TokenCounter.PRICE_TABLE


class TestLLMTool:
    """Tests for create_llm_tool and its integration with Agent."""

    def test_create_llm_tool_returns_tool(self):
        """create_llm_tool() returns a Tool instance."""
        from agentwork import Tool

        provider = OpenAIProvider()
        llm_tool = create_llm_tool(provider)
        assert isinstance(llm_tool, Tool)
        assert llm_tool.name == "llm"

    def test_create_llm_tool_custom_name(self):
        """create_llm_tool() accepts custom name and description."""
        provider = OpenAIProvider()
        llm_tool = create_llm_tool(
            provider, name="my_llm", description="Custom LLM tool"
        )
        assert llm_tool.name == "my_llm"
        assert llm_tool.description == "Custom LLM tool"

    def test_llm_tool_execute(self):
        """LLM tool executes and returns content."""
        provider = OpenAIProvider()
        llm_tool = create_llm_tool(provider)
        result = llm_tool.execute(prompt="test prompt")
        assert result.status.value == "success"
        assert "OpenAI stub response" in result.output

    def test_llm_tool_in_agent(self):
        """LLM tool works when registered in an Agent."""
        provider = OpenAIProvider()
        llm_tool = create_llm_tool(provider)
        agent = Agent(name="TestAgent", tools=[llm_tool])
        result = agent.execute("llm", {"prompt": "What is AI?"})
        assert result.status.value == "success"
        assert "OpenAI stub response" in result.output

    def test_llm_tool_with_anthropic(self):
        """LLM tool works with Anthropic provider."""
        provider = AnthropicProvider()
        llm_tool = create_llm_tool(provider, name="claude")
        agent = Agent(name="TestAgent", tools=[llm_tool])
        result = agent.execute("claude", {"prompt": "Explain Python"})
        assert result.status.value == "success"
        assert "Anthropic stub response" in result.output
