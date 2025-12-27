"""
Base Agent Class

Foundation for all AI sub-agents.
Provides common functionality for Claude API integration.

PRD-017: Removed logging.basicConfig() call to avoid conflicts with uvicorn's
logging configuration. App-wide logging should be configured centrally in app.py.

PRD-034: Added retry logic with exponential backoff to call_claude() method
for improved reliability during transient API failures.
"""

import os
import json
import logging
import time
import base64
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from anthropic import Anthropic
from dotenv import load_dotenv

# Get logger (don't configure here - let app.py handle logging config)
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

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-5-20250514"):
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
        expect_json: bool = True,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Make a call to Claude API with retry logic.

        PRD-034: Added exponential backoff retry for transient failures.

        Args:
            prompt: User prompt to send
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 = deterministic)
            expect_json: Whether to expect JSON response
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            Parsed response (dict if JSON, string otherwise)

        Raises:
            Exception: If API call fails after all retries
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                logger.debug(f"Calling Claude with prompt length: {len(prompt)} (attempt {attempt + 1}/{max_retries})")

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
                last_exception = e

                if attempt < max_retries - 1:
                    # Calculate delay with exponential backoff (1s, 2s, 4s, ..., max 30s)
                    delay = min(2 ** attempt, 30)
                    logger.warning(
                        f"Claude API attempt {attempt + 1}/{max_retries} failed: {str(e)}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Claude API failed after {max_retries} attempts: {str(e)}")

        # All retries exhausted, raise the last exception
        raise last_exception

    def call_claude_vision(
        self,
        prompt: str,
        image_path: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        expect_json: bool = True,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Make a call to Claude Vision API with an image.

        PRD-039: Added for chart and compass image analysis.

        Args:
            prompt: User prompt describing what to extract
            image_path: Path to the image file
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 = deterministic)
            expect_json: Whether to expect JSON response
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            Parsed response (dict if JSON, string otherwise)

        Raises:
            Exception: If API call fails after all retries
            FileNotFoundError: If image file doesn't exist
        """
        # Validate image exists
        image_file = Path(image_path)
        if not image_file.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Read and encode image
        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")

        # Determine media type
        suffix = image_file.suffix.lower()
        media_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        media_type = media_type_map.get(suffix, "image/png")

        last_exception = None

        for attempt in range(max_retries):
            try:
                logger.debug(f"Calling Claude Vision for {image_path} (attempt {attempt + 1}/{max_retries})")

                # Build messages with image content
                messages = [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }]

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
                logger.debug(f"Received vision response length: {len(response_text)}")

                # Parse JSON if expected
                if expect_json:
                    return self._parse_json_response(response_text)
                else:
                    return {"response": response_text}

            except Exception as e:
                last_exception = e

                if attempt < max_retries - 1:
                    delay = min(2 ** attempt, 30)
                    logger.warning(
                        f"Claude Vision API attempt {attempt + 1}/{max_retries} failed: {str(e)}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Claude Vision API failed after {max_retries} attempts: {str(e)}")

        raise last_exception

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
