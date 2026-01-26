"""
Confluence Hub API Client

Provides access to the research synthesis and content APIs.
"""

import httpx
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta


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
        """Get the latest research synthesis with full detail (tier=3).

        PRD-041: Always request tier=3 to get all V4 data including:
        - Executive summary (tier 1)
        - Source breakdowns with YouTube channel granularity (tier 2)
        - Per-content summaries (tier 3)
        """
        return self._request("GET", "/api/synthesis/latest?tier=3")

    def get_synthesis_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent synthesis history."""
        return self._request("GET", f"/api/synthesis/history?limit={limit}")

    def search_content(
        self,
        query: str,
        source: Optional[str] = None,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Search across collected research content.

        Note: This uses the status/overview endpoint and filters.
        For a full search, we'd need to add a search endpoint to the API.
        """
        # Get recent analyzed content
        params = {"days": days}
        if source:
            params["source"] = source

        try:
            # Try the debug endpoint which has content details
            result = self._request("GET", "/api/synthesis/debug")
            content_items = result.get("content_items", [])

            # Filter by query (simple text match)
            query_lower = query.lower()
            matches = []
            for item in content_items:
                # Search in title, content, themes
                searchable = " ".join([
                    str(item.get("title", "")),
                    str(item.get("content_text", "")),
                    str(item.get("summary", "")),
                    " ".join(item.get("themes", []))
                ]).lower()

                if query_lower in searchable:
                    # Filter by source if specified
                    if source and item.get("source", "").lower() != source.lower():
                        continue
                    matches.append({
                        "source": item.get("source"),
                        "title": item.get("title"),
                        "date": item.get("timestamp") or item.get("collected_at"),
                        "themes": item.get("themes", []),
                        "sentiment": item.get("sentiment"),
                        "summary": str(item.get("summary", item.get("content_text", "")))[:500]
                    })

            return matches[:20]  # Limit results

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
        return self.search_content("", source=source, days=days)

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


# Convenience functions for extracting synthesis components

def extract_confluence_zones(synthesis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract confluence zones from synthesis."""
    return synthesis.get("confluence_zones", [])


def extract_conflicts(synthesis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract conflict watch items from synthesis."""
    return synthesis.get("conflict_watch", [])


def extract_attention_priorities(synthesis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract attention priorities from synthesis."""
    return synthesis.get("attention_priorities", [])


def extract_source_stances(synthesis: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Extract source stances from synthesis.

    PRD-041: V4 synthesis uses source_breakdowns instead of source_stances.
    This function falls back to source_breakdowns when source_stances is empty,
    normalizing the data structure for consistent MCP tool output.
    """
    # First try V3 source_stances
    stances = synthesis.get("source_stances", {})
    if stances:
        return stances

    # Fall back to V4 source_breakdowns
    breakdowns = synthesis.get("source_breakdowns", {})
    if not breakdowns:
        return {}

    # Normalize V4 breakdowns to match V3 stance structure
    normalized = {}
    for source_name, data in breakdowns.items():
        # Format display name for YouTube channels (youtube:Channel Name -> Channel Name)
        display_name = source_name
        if source_name.startswith("youtube:"):
            display_name = source_name.split(":", 1)[1]

        normalized[source_name] = {
            "current_stance_narrative": data.get("summary", ""),
            "summary": data.get("summary", ""),
            "key_insights": data.get("key_insights", []),
            "themes": data.get("themes", []),
            "overall_bias": data.get("overall_bias", "neutral"),
            "content_count": data.get("content_count", 0),
            "display_name": display_name
        }

    return normalized


def extract_catalyst_calendar(synthesis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract catalyst calendar from synthesis."""
    return synthesis.get("catalyst_calendar", [])


def extract_re_review_recommendations(synthesis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract re-review recommendations from synthesis."""
    return synthesis.get("re_review_recommendations", [])


def extract_executive_summary(synthesis: Dict[str, Any]) -> Dict[str, Any]:
    """Extract executive summary from synthesis."""
    return synthesis.get("executive_summary", {})
