"""
API Client for MCP Server

Fetches data from Railway API instead of local database.
Part of PRD-016: MCP Server API Proxy Refactor.

This module provides a thin HTTP client that allows MCP tools to fetch
data from the production Railway API, enabling Claude Desktop to access
production data regardless of where it runs.
"""

import os
import logging
from typing import Optional, Dict, Any, List

import httpx

from .config import (
    API_BASE_URL,
    AUTH_USERNAME,
    AUTH_PASSWORD,
    REQUEST_TIMEOUT
)

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Custom exception for API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, hint: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.hint = hint
        super().__init__(self.message)


class APIClient:
    """
    HTTP client for Railway API.

    Provides authenticated access to the Confluence Hub API endpoints.
    Handles error cases gracefully with helpful error messages.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        """
        Initialize API client.

        Args:
            base_url: API base URL (defaults to config value)
            username: Auth username (defaults to config value)
            password: Auth password (defaults to config value)
            timeout: Request timeout in seconds (defaults to config value)
        """
        self.base_url = (base_url or API_BASE_URL).rstrip("/")
        self.username = username or AUTH_USERNAME
        self.password = password or AUTH_PASSWORD
        self.timeout = timeout or REQUEST_TIMEOUT

        # Set up auth if password is provided
        self.auth = None
        if self.password:
            self.auth = (self.username, self.password)

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        retry_count: int = 1
    ) -> Dict[str, Any]:
        """
        Make HTTP request to API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON body for POST/PUT requests
            retry_count: Number of retries on transient failures

        Returns:
            Response JSON as dictionary

        Raises:
            APIError: On network/HTTP errors with helpful messages
        """
        url = f"{self.base_url}{endpoint}"

        # Filter out None values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        last_error = None

        for attempt in range(retry_count + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.request(
                        method=method,
                        url=url,
                        params=params,
                        json=json_data,
                        auth=self.auth
                    )

                    # Handle HTTP errors
                    if response.status_code == 401:
                        raise APIError(
                            message="Authentication failed",
                            status_code=401,
                            hint="Check AUTH_USERNAME and AUTH_PASSWORD environment variables"
                        )

                    if response.status_code == 404:
                        raise APIError(
                            message=f"Endpoint not found: {endpoint}",
                            status_code=404,
                            hint="The API endpoint may not exist or has been moved"
                        )

                    if response.status_code >= 500:
                        raise APIError(
                            message=f"Server error: {response.status_code}",
                            status_code=response.status_code,
                            hint="The API server may be experiencing issues"
                        )

                    response.raise_for_status()

                    # Parse JSON response
                    try:
                        return response.json()
                    except ValueError:
                        return {"raw_response": response.text}

            except httpx.ConnectError as e:
                last_error = APIError(
                    message="Cannot connect to Confluence Hub API",
                    hint=f"Check RAILWAY_API_URL ({self.base_url}) and network connection"
                )
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")

            except httpx.TimeoutException as e:
                last_error = APIError(
                    message="Request timed out",
                    hint=f"The API took longer than {self.timeout}s to respond"
                )
                logger.warning(f"Timeout on attempt {attempt + 1}: {e}")

            except httpx.HTTPStatusError as e:
                # Re-raise as APIError if not already handled
                raise APIError(
                    message=f"HTTP error: {e.response.status_code}",
                    status_code=e.response.status_code
                )

            except APIError:
                raise

            except Exception as e:
                last_error = APIError(
                    message=f"Unexpected error: {str(e)}",
                    hint="Check logs for details"
                )
                logger.error(f"Unexpected error: {e}", exc_info=True)

        # All retries exhausted
        if last_error:
            raise last_error

        raise APIError(message="Request failed after all retries")

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 1
    ) -> Dict[str, Any]:
        """
        Make GET request to API.

        Args:
            endpoint: API endpoint path (e.g., "/api/synthesis/latest")
            params: Query parameters
            retry_count: Number of retries on transient failures

        Returns:
            Response JSON as dictionary
        """
        return self._request("GET", endpoint, params=params, retry_count=retry_count)

    def post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 1
    ) -> Dict[str, Any]:
        """
        Make POST request to API.

        Args:
            endpoint: API endpoint path
            json_data: JSON body data
            params: Query parameters
            retry_count: Number of retries on transient failures

        Returns:
            Response JSON as dictionary
        """
        return self._request(
            "POST",
            endpoint,
            params=params,
            json_data=json_data,
            retry_count=retry_count
        )

    def health_check(self) -> bool:
        """
        Check if API is reachable and healthy.

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            # Health endpoint doesn't require auth
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False


def handle_api_error(error: APIError) -> Dict[str, Any]:
    """
    Convert APIError to user-friendly response dict.

    Args:
        error: The APIError exception

    Returns:
        Dictionary with error information suitable for MCP tool response
    """
    result = {
        "error": error.message,
        "success": False
    }

    if error.status_code:
        result["status_code"] = error.status_code

    if error.hint:
        result["hint"] = error.hint

    return result


# Global API client instance
# This will be initialized with config values from config.py
api = APIClient()
