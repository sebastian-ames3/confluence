"""
Data Helper Utilities

PRD-047: Data Integrity & Resilience
Provides null-safe access patterns for database fields like analysis_result.
"""

import json
import logging
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)


def safe_get_analysis_result(
    analyzed_content,
    max_length: Optional[int] = None
) -> Dict[str, Any]:
    """
    Safely get analysis_result with null and type handling.

    Handles cases where:
    - analyzed_content is None
    - analysis_result is None
    - analysis_result is a JSON string (parses it)
    - analysis_result is already a dict

    Args:
        analyzed_content: AnalyzedContent ORM object or None
        max_length: Optional max length for string values

    Returns:
        Dict with analysis data, or empty dict if unavailable
    """
    if not analyzed_content:
        return {}

    result = analyzed_content.analysis_result
    if not result:
        return {}

    # If it's a string, try to parse as JSON
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
            return parsed if isinstance(parsed, dict) else {"raw": result}
        except json.JSONDecodeError:
            # Return raw string wrapped in dict
            truncated = result[:max_length] if max_length and len(result) > max_length else result
            return {"raw": truncated}

    # If already a dict, return as-is
    if isinstance(result, dict):
        return result

    # Unknown type, return empty
    logger.warning(f"Unexpected analysis_result type: {type(result)}")
    return {}


def safe_get_analysis_preview(
    analyzed_content,
    max_length: int = 500
) -> str:
    """
    Safely get a text preview of analysis_result.

    Args:
        analyzed_content: AnalyzedContent ORM object or None
        max_length: Maximum characters for preview (default 500)

    Returns:
        String preview of analysis, or "[Not analyzed]" if unavailable
    """
    if not analyzed_content:
        return "[Not analyzed]"

    result = analyzed_content.analysis_result
    if not result:
        return "[Not analyzed]"

    # Convert to string if needed
    if isinstance(result, dict):
        result = json.dumps(result)

    # Ensure it's a string
    if not isinstance(result, str):
        result = str(result)

    # Truncate if needed
    if len(result) > max_length:
        return result[:max_length] + "..."

    return result


def get_analysis_field(
    content,
    field: str,
    default: Any = None
) -> Any:
    """
    Safely get a specific field from analysis_result.

    Args:
        content: AnalyzedContent ORM object or None
        field: Field name to extract (e.g., "sentiment", "themes")
        default: Default value if field not found

    Returns:
        Field value or default
    """
    if not content:
        return default

    result = content.analysis_result
    if not result:
        return default

    # Parse if string
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            return default

    # Get field from dict
    if isinstance(result, dict):
        return result.get(field, default)

    return default


def safe_json_loads(
    data: Optional[str],
    default: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Safely parse JSON string with default fallback.

    Args:
        data: JSON string or None
        default: Default value if parsing fails (defaults to {})

    Returns:
        Parsed dict or default
    """
    if default is None:
        default = {}

    if not data:
        return default

    if isinstance(data, dict):
        return data

    try:
        parsed = json.loads(data)
        return parsed if isinstance(parsed, dict) else default
    except (json.JSONDecodeError, TypeError):
        return default
