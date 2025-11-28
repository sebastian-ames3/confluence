"""
Base Agent Class

Foundation for all AI sub-agents.
Provides common functionality for Claude API integration.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from anthropic import Anthropic
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from project root
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")


class BaseAgent:
    """
    Base class for all AI agents.

    Provides:
    - Claude API client initialization
    - Standard prompt formatting
    - Response validation and parsing
    - Error handling
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize base agent.

        Args:
            api_key: Claude API key (defaults to CLAUDE_API_KEY env var)
            model: Claude model to use
        """
        self.api_key = api_key or os.getenv("CLAUDE_API_KEY")
        if not self.api_key:
            raise ValueError("Claude API key is required. Set CLAUDE_API_KEY environment variable.")

        self.model = model
        self.client = Anthropic(api_key=self.api_key)
        logger.info(f"Initialized {self.__class__.__name__} with model {self.model}")

    def call_claude(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        expect_json: bool = True
    ) -> Dict[str, Any]:
        """
        Make a call to Claude API.

        Args:
            prompt: User prompt to send
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 = deterministic)
            expect_json: Whether to expect JSON response

        Returns:
            Parsed response (dict if JSON, string otherwise)

        Raises:
            Exception: If API call fails or response is invalid
        """
        try:
            logger.debug(f"Calling Claude with prompt length: {len(prompt)}")

            # Build messages
            messages = [{"role": "user", "content": prompt}]

            # Make API call
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt if system_prompt else "",
                messages=messages
            )

            # Extract text content
            response_text = response.content[0].text
            logger.debug(f"Received response length: {len(response_text)}")

            # Parse JSON if expected
            if expect_json:
                return self._parse_json_response(response_text)
            else:
                return {"response": response_text}

        except Exception as e:
            logger.error(f"Claude API call failed: {str(e)}")
            raise

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON response from Claude.

        Handles cases where Claude returns markdown code blocks or
        includes explanatory text before/after JSON.

        Args:
            response_text: Raw response text from Claude

        Returns:
            Parsed JSON as dictionary

        Raises:
            ValueError: If JSON parsing fails
        """
        try:
            # Try direct parsing first
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Look for JSON in code blocks
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
                return json.loads(json_str)
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
                return json.loads(json_str)
            else:
                # Try to find JSON object/array boundaries
                for start_char, end_char in [('{', '}'), ('[', ']')]:
                    start = response_text.find(start_char)
                    end = response_text.rfind(end_char)
                    if start != -1 and end != -1:
                        json_str = response_text[start:end+1]
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError:
                            continue

                logger.error(f"Could not parse JSON from response: {response_text[:200]}")
                raise ValueError("Failed to parse JSON from Claude response")

    def validate_response_schema(self, response: Dict[str, Any], required_fields: list) -> bool:
        """
        Validate that response contains required fields.

        Args:
            response: Parsed response dictionary
            required_fields: List of required field names

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        missing_fields = [field for field in required_fields if field not in response]
        if missing_fields:
            raise ValueError(f"Response missing required fields: {missing_fields}")
        return True

    def analyze(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Main analysis method to be implemented by subclasses.

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement analyze() method")
