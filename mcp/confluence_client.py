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
        """Get the latest v3 research synthesis."""
        return self._request("GET", "/api/synthesis/latest")

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
    """Extract source stances from synthesis."""
    return synthesis.get("source_stances", {})


def extract_catalyst_calendar(synthesis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract catalyst calendar from synthesis."""
    return synthesis.get("catalyst_calendar", [])


def extract_re_review_recommendations(synthesis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract re-review recommendations from synthesis."""
    return synthesis.get("re_review_recommendations", [])


def extract_executive_summary(synthesis: Dict[str, Any]) -> Dict[str, Any]:
    """Extract executive summary from synthesis."""
    return synthesis.get("executive_summary", {})
