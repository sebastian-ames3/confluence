"""
Confluence Hub API Client

Provides access to the research synthesis and content APIs.
"""

import httpx
import logging
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ConfluenceClient:
    """Client for interacting with Confluence Hub API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        self.base_url = base_url or os.getenv("CONFLUENCE_API_URL", "https://confluence-production-a32e.up.railway.app")
        self.username = username or os.getenv("CONFLUENCE_USERNAME")
        self.password = password or os.getenv("CONFLUENCE_PASSWORD")

        if not self.username or not self.password:
            raise ValueError("CONFLUENCE_USERNAME and CONFLUENCE_PASSWORD must be set")

        self.auth = (self.username, self.password)

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an authenticated request to the API."""
        url = f"{self.base_url}{endpoint}"
        with httpx.Client(timeout=30.0) as client:
            response = client.request(method, url, auth=self.auth, **kwargs)
            response.raise_for_status()
            return response.json()

    def get_latest_synthesis(self) -> Dict[str, Any]:
        """Get the latest research synthesis with full detail."""
        return self._request("GET", "/api/synthesis/latest")

    def get_synthesis_history(self, limit: int = 5, offset: int = 0) -> List[Dict[str, Any]]:
        """Get recent synthesis history."""
        params = f"limit={limit}"
        if offset > 0:
            params += f"&offset={offset}"
        return self._request("GET", f"/api/synthesis/history?{params}")

    def get_synthesis_by_id(self, synthesis_id: int) -> Dict[str, Any]:
        """Get a specific synthesis by ID."""
        return self._request("GET", f"/api/synthesis/{synthesis_id}")

    def search_content(
        self,
        query: str,
        source: Optional[str] = None,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Search across collected research content.

        Uses the /api/search/content endpoint which does server-side
        SQL search across content text, metadata, and themes.
        """
        params = {"q": query, "days": days, "limit": 50}
        if source:
            params["source"] = source

        try:
            result = self._request("GET", "/api/search/content", params=params)
            api_results = result.get("results", [])

            # Normalize to consistent format for MCP
            matches = []
            for item in api_results:
                matches.append({
                    "id": item.get("id"),
                    "source": item.get("source"),
                    "title": item.get("title"),
                    "date": item.get("date"),
                    "type": item.get("type"),
                    "themes": item.get("themes", []),
                    "sentiment": item.get("sentiment"),
                    "conviction": item.get("conviction"),
                    "summary": item.get("analysis_summary") or item.get("snippet", "")
                })

            return matches

        except Exception as e:
            return [{"error": str(e)}]

    def get_status_overview(self) -> Dict[str, Any]:
        """Get status overview including source counts."""
        return self._request("GET", "/api/synthesis/status/overview")

    def get_source_content(
        self,
        source: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get recent content from a specific source."""
        try:
            result = self._request("GET", f"/api/search/recent/{source}", params={"days": days})
            return result.get("items", [])
        except Exception as e:
            return [{"error": str(e)}]

    # =====================================================
    # THEME TRACKING API (PRD-024)
    # =====================================================

    def get_themes(
        self,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get investment themes being tracked.

        Args:
            status: Filter by status (emerging, active, evolved, dormant)
            limit: Maximum number of themes to return
        """
        params = {"limit": limit}
        if status:
            params["status"] = status

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return self._request("GET", f"/api/themes?{query_string}")

    def get_theme(self, theme_id: int) -> Dict[str, Any]:
        """Get a specific theme by ID with full details."""
        return self._request("GET", f"/api/themes/{theme_id}")

    def get_themes_summary(self) -> Dict[str, Any]:
        """Get theme statistics summary."""
        return self._request("GET", "/api/themes/summary")

    def get_active_themes(self) -> List[Dict[str, Any]]:
        """Get currently active themes (emerging or active status)."""
        emerging = self.get_themes(status="emerging")
        active = self.get_themes(status="active")
        return active + emerging

    # PRD-039: Symbol-Level Confluence Methods
    def get_all_symbols(self) -> Dict[str, Any]:
        """Get all tracked symbols with state summary."""
        return self._request("GET", "/api/symbols")

    def get_symbol_detail(self, symbol: str) -> Dict[str, Any]:
        """Get full detail for one symbol."""
        return self._request("GET", f"/api/symbols/{symbol}")

    def get_symbol_levels(
        self,
        symbol: str,
        source: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all active price levels for a symbol."""
        params = {}
        if source:
            params["source"] = source
        endpoint = f"/api/symbols/{symbol}/levels"
        if params:
            query_string = "&".join(f"{k}={v}" for k, v in params.items())
            endpoint = f"{endpoint}?{query_string}"
        return self._request("GET", endpoint)

    def get_confluence_opportunities(self) -> Dict[str, Any]:
        """Get symbols where KT and Discord are aligned (high confluence)."""
        return self._request("GET", "/api/symbols/confluence/opportunities")

    # PRD-044: Synthesis Quality Methods
    def get_synthesis_quality(self, synthesis_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get quality evaluation for a synthesis.

        Args:
            synthesis_id: Optional specific synthesis ID. If not provided, gets latest.

        Returns quality score including:
        - Overall score (0-100) and letter grade
        - Individual criterion scores (0-3 each)
        - Flags for low-scoring criteria
        - Prompt suggestions for improvement
        """
        if synthesis_id:
            return self._request("GET", f"/api/quality/{synthesis_id}")
        else:
            return self._request("GET", "/api/quality/latest")

    def get_quality_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get quality score trends over time."""
        return self._request("GET", f"/api/quality/trends?days={days}")

    def get_quality_flagged(self, limit: int = 10) -> Dict[str, Any]:
        """Get syntheses with quality flags."""
        return self._request("GET", f"/api/quality/flagged?limit={limit}")

    def get_source_health(self) -> Dict[str, Any]:
        """Get health status for all sources."""
        return self._request("GET", "/api/health/sources")

    def get_active_alerts(self, include_acknowledged: bool = False) -> Dict[str, Any]:
        """Get active system alerts."""
        params = f"include_acknowledged={'true' if include_acknowledged else 'false'}"
        return self._request("GET", f"/api/health/alerts?{params}")

    def get_theme_evolution(self, theme_id: int) -> Dict[str, Any]:
        """Get historical evolution data for a theme."""
        return self._request("GET", f"/api/dashboard/historical/{theme_id}")

    # =====================================================
    # CONTENT BROWSING API (PRD-051: Individual Content Access)
    # =====================================================

    def list_recent_content(
        self,
        source: Optional[str] = None,
        content_type: Optional[str] = None,
        days: int = 7,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        List recent content items across all sources.

        Args:
            source: Optional filter by source (youtube, 42macro, discord, kt_technical, substack)
            content_type: Optional filter by type (video, pdf, text, image)
            days: Number of days to look back (default 7)
            limit: Maximum items to return (default 20)

        Returns:
            Dictionary with list of content items including:
            - id: Content ID for use with get_content_detail
            - title: Content title
            - source: Source name
            - channel: YouTube channel name if applicable
            - type: Content type
            - date: Collection date
            - summary: Brief summary
            - themes: Extracted themes
            - has_transcript: Whether full transcript is available
        """
        params = {"days": days, "limit": limit}
        if source:
            params["source"] = source
        if content_type:
            params["content_type"] = content_type

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return self._request("GET", f"/api/search/recent?{query_string}")

    def get_content_detail(self, content_id: int) -> Dict[str, Any]:
        """
        Get full details for a specific content item.

        This enables discussion of individual videos, PDFs, and articles
        by retrieving the full transcript/text and analysis.

        Args:
            content_id: ID of the content item (from list_recent_content)

        Returns:
            Dictionary with full content details including:
            - id: Content ID
            - source: Source name
            - type: Content type (video, pdf, text, etc.)
            - title: Content title
            - url: Original URL
            - content_text: Full transcript/text content
            - metadata: Video-specific info (channel, duration, views)
            - analysis: AI analysis results (summary, key_points, themes, sentiment)
        """
        return self._request("GET", f"/api/search/content/{content_id}")


# Convenience functions for extracting synthesis components
# PRD-049: Added type validation to return structured errors


def extract_confluence_zones(synthesis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract confluence zones from synthesis."""
    if not isinstance(synthesis, dict):
        return []
    zones = synthesis.get("confluence_zones")
    if not isinstance(zones, list):
        return []
    return zones


def extract_conflicts(synthesis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract conflict watch items from synthesis."""
    if not isinstance(synthesis, dict):
        return []
    conflicts = synthesis.get("conflict_watch")
    if not isinstance(conflicts, list):
        return []
    return conflicts


def extract_attention_priorities(synthesis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract attention priorities from synthesis."""
    if not isinstance(synthesis, dict):
        return []
    priorities = synthesis.get("attention_priorities")
    if not isinstance(priorities, list):
        return []
    return priorities


def extract_source_breakdowns(synthesis: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Extract source breakdowns from synthesis."""
    if not isinstance(synthesis, dict):
        return {}
    breakdowns = synthesis.get("source_breakdowns")
    if not isinstance(breakdowns, dict):
        return {}
    return breakdowns


def extract_catalyst_calendar(synthesis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract catalyst calendar from synthesis.

    PRD-049: Added type validation.
    """
    if not isinstance(synthesis, dict):
        return []
    calendar = synthesis.get("catalyst_calendar")
    if not isinstance(calendar, list):
        return []
    return calendar


def extract_re_review_recommendations(synthesis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract re-review recommendations from synthesis.

    PRD-049: Added type validation.
    """
    if not isinstance(synthesis, dict):
        return []
    recommendations = synthesis.get("re_review_recommendations")
    if not isinstance(recommendations, list):
        return []
    return recommendations


def extract_executive_summary(synthesis: Dict[str, Any]) -> Dict[str, Any]:
    """Extract executive summary from synthesis.

    PRD-049: Added type validation.
    """
    if not isinstance(synthesis, dict):
        return {}
    summary = synthesis.get("executive_summary")
    if not isinstance(summary, dict):
        return {}
    return summary
