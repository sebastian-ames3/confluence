"""Test agent error handling with malformed Claude responses."""
import os
import json
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_env():
    """Set up mock environment variables."""
    with patch.dict(os.environ, {"CLAUDE_API_KEY": "test-key-12345"}):
        yield


@pytest.fixture
def agent(mock_env):
    """Create a BaseAgent with mocked API key."""
    with patch("agents.base_agent.Anthropic"):
        from agents.base_agent import BaseAgent

        return BaseAgent(api_key="test-key")


class TestBaseAgentJSONParsing:
    """Test JSON parsing with various response formats."""

    def test_parses_clean_json(self, agent):
        result = agent._parse_json_response('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parses_json_array(self, agent):
        result = agent._parse_json_response('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_parses_json_in_code_block(self, agent):
        result = agent._parse_json_response('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_parses_json_in_generic_code_block(self, agent):
        result = agent._parse_json_response('```\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_parses_json_with_surrounding_text(self, agent):
        text = 'Here is the result: {"key": "value"} Hope that helps!'
        result = agent._parse_json_response(text)
        assert result == {"key": "value"}

    def test_parses_nested_json(self, agent):
        nested = {"outer": {"inner": [1, 2, 3]}, "flat": "value"}
        result = agent._parse_json_response(json.dumps(nested))
        assert result == nested

    def test_raises_on_invalid_json(self, agent):
        with pytest.raises(ValueError):
            agent._parse_json_response("this is not json at all")

    def test_raises_on_empty_string(self, agent):
        with pytest.raises((ValueError, json.JSONDecodeError)):
            agent._parse_json_response("")

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            ('{"a": 1}', {"a": 1}),
            ("  {  }  ", {}),
            ('{"nested": {"a": 1}}', {"nested": {"a": 1}}),
        ],
    )
    def test_various_valid_json(self, agent, input_text, expected):
        result = agent._parse_json_response(input_text)
        assert result == expected


class TestBaseAgentResponseValidation:
    """Test response schema validation."""

    def test_validate_with_all_required_fields(self, agent):
        response = {"name": "test", "value": 42, "status": "ok"}
        assert agent.validate_response_schema(response, ["name", "value", "status"])

    def test_validate_with_missing_fields_raises(self, agent):
        response = {"name": "test"}
        with pytest.raises(ValueError, match="missing required fields"):
            agent.validate_response_schema(response, ["name", "value"])

    def test_validate_with_empty_response_raises(self, agent):
        with pytest.raises(ValueError, match="missing required fields"):
            agent.validate_response_schema({}, ["name"])

    def test_validate_with_no_required_fields(self, agent):
        assert agent.validate_response_schema({"anything": 1}, [])


class TestBaseAgentRetryLogic:
    """Test that retry logic handles different error types correctly."""

    def test_retries_on_api_timeout(self, mock_env):
        """Timeout errors should be retried."""
        with patch("agents.base_agent.Anthropic") as mock_cls:
            from agents.base_agent import BaseAgent

            agent = BaseAgent(api_key="test-key")

            # Simulate timeout errors
            from anthropic import APITimeoutError

            mock_request = MagicMock()
            agent.client.messages.create.side_effect = APITimeoutError(
                request=mock_request
            )

            with pytest.raises(APITimeoutError):
                agent.call_claude("test prompt", max_retries=2)

            # Should have been called twice (original + 1 retry)
            assert agent.client.messages.create.call_count == 2

    def test_retries_on_rate_limit(self, mock_env):
        """Rate limit errors should be retried."""
        with patch("agents.base_agent.Anthropic") as mock_cls:
            from agents.base_agent import BaseAgent

            agent = BaseAgent(api_key="test-key")

            from anthropic import RateLimitError

            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.headers = {}
            agent.client.messages.create.side_effect = RateLimitError(
                message="rate limited",
                response=mock_response,
                body=None,
            )

            with pytest.raises(RateLimitError):
                agent.call_claude("test prompt", max_retries=2)

            assert agent.client.messages.create.call_count == 2

    def test_successful_response_returns_parsed_json(self, mock_env):
        """A successful response should be parsed and returned."""
        with patch("agents.base_agent.Anthropic"):
            from agents.base_agent import BaseAgent

            agent = BaseAgent(api_key="test-key")

            mock_response = MagicMock()
            mock_response.content = [MagicMock(text='{"result": "success"}')]
            agent.client.messages.create.return_value = mock_response

            result = agent.call_claude("test prompt", expect_json=True)
            assert result == {"result": "success"}

    def test_successful_response_returns_text_when_no_json(self, mock_env):
        """When expect_json=False, raw text should be returned."""
        with patch("agents.base_agent.Anthropic"):
            from agents.base_agent import BaseAgent

            agent = BaseAgent(api_key="test-key")

            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Hello, world!")]
            agent.client.messages.create.return_value = mock_response

            result = agent.call_claude("test prompt", expect_json=False)
            # call_claude wraps text responses in a dict
            assert result == {"response": "Hello, world!"}
