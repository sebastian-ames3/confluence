"""
Theme Extractor Agent (PRD-024)

Extracts themes from synthesis content and matches them against existing themes.
Uses Claude for semantic matching to consolidate similar themes.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from agents.base_agent import BaseAgent
from backend.utils.sanitization import wrap_content_for_prompt, sanitize_content_text

logger = logging.getLogger(__name__)


class ThemeExtractorAgent(BaseAgent):
    """
    Agent for extracting and matching investment themes.

    Called after synthesis generation to:
    1. Extract themes from the synthesis output
    2. Match against existing themes using semantic similarity
    3. Create new themes or add evidence to existing ones
    """

    SYSTEM_PROMPT = """You are a theme extraction and matching agent for investment research.

Your job is to:
1. Identify distinct macro/investment themes from synthesis content
2. Match new themes against existing themes using semantic similarity
3. Determine if a theme is truly new or a variation of an existing theme

THEME MATCHING CRITERIA:
- Themes about the same underlying concept should match (e.g., "Fed hawkish cut" matches "FOMC 25bp with higher terminal rate")
- Consider temporal context - a theme about "December FOMC" and "Fed meeting" in December are the same
- Themes can evolve - if "FOMC uncertainty" becomes "hawkish cut consensus", flag as evolution

OUTPUT FORMAT: JSON only, no explanation."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Theme Extractor Agent."""
        super().__init__(api_key=api_key)

    def extract_themes_from_synthesis(
        self,
        synthesis_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract themes from a v3 synthesis output.

        Args:
            synthesis_data: Full synthesis JSON (v3 format)

        Returns:
            List of extracted themes with source attribution
        """
        # Build extraction prompt
        prompt = self._build_extraction_prompt(synthesis_data)

        try:
            response = self.call_claude(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
                max_tokens=2000,
                temperature=0.1,
                expect_json=True
            )

            themes = response.get("themes", [])
            logger.info(f"Extracted {len(themes)} themes from synthesis")
            return themes

        except Exception as e:
            logger.error(f"Theme extraction failed: {str(e)}")
            return []

    def _build_extraction_prompt(self, synthesis_data: Dict[str, Any]) -> str:
        """Build prompt for theme extraction."""
        # Extract relevant sections
        exec_summary = synthesis_data.get("executive_summary", {})
        confluence_zones = synthesis_data.get("confluence_zones", [])
        conflict_watch = synthesis_data.get("conflict_watch", [])
        attention_priorities = synthesis_data.get("attention_priorities", [])
        source_breakdowns = synthesis_data.get("source_breakdowns", {})

        # Build synthesis text and wrap for injection protection
        synthesis_text = (
            f"## Executive Summary\n{json.dumps(exec_summary, indent=2)}\n\n"
            f"## Confluence Zones\n{json.dumps(confluence_zones, indent=2)}\n\n"
            f"## Conflicts\n{json.dumps(conflict_watch, indent=2)}\n\n"
            f"## Attention Priorities\n{json.dumps(attention_priorities, indent=2)}\n\n"
            f"## Source Breakdowns\n{json.dumps(source_breakdowns, indent=2)}"
        )
        wrapped_synthesis = wrap_content_for_prompt(
            sanitize_content_text(synthesis_text), max_chars=30000
        )

        prompt = f"""Extract the key investment themes from this synthesis:

{wrapped_synthesis}

---

Extract distinct themes. For each theme, identify:
1. A clear, concise theme name (e.g., "FOMC hawkish cut expectations")
2. Which sources discuss this theme
3. A brief description
4. Related catalysts if any
5. Is this theme emerging (1-2 sources) or established (3+ sources)?

Respond with JSON:
{{
  "themes": [
    {{
      "name": "Theme name",
      "description": "1-2 sentence description",
      "sources": {{"source_name": "what they said about it"}},
      "catalysts": ["catalyst if any"],
      "status": "emerging" or "active"
    }}
  ]
}}"""

        return prompt

    def match_themes(
        self,
        new_themes: List[Dict[str, Any]],
        existing_themes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Match newly extracted themes against existing themes.

        Args:
            new_themes: Themes extracted from current synthesis
            existing_themes: Existing themes from database

        Returns:
            List of match results with actions (create, update, evolve, merge_suggestion)
        """
        if not new_themes:
            return []

        if not existing_themes:
            # No existing themes, all are new
            return [
                {
                    "new_theme": theme,
                    "action": "create",
                    "match_id": None,
                    "is_evolution": False
                }
                for theme in new_themes
            ]

        # Build matching prompt
        prompt = self._build_matching_prompt(new_themes, existing_themes)

        try:
            response = self.call_claude(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
                max_tokens=2000,
                temperature=0.0,  # Deterministic matching
                expect_json=True
            )

            matches = response.get("matches", [])
            logger.info(f"Matched {len(matches)} themes")
            return matches

        except Exception as e:
            logger.error(f"Theme matching failed: {str(e)}")
            # Fallback: treat all as new
            return [
                {
                    "new_theme": theme,
                    "action": "create",
                    "match_id": None,
                    "is_evolution": False
                }
                for theme in new_themes
            ]

    def _build_matching_prompt(
        self,
        new_themes: List[Dict[str, Any]],
        existing_themes: List[Dict[str, Any]]
    ) -> str:
        """Build prompt for theme matching."""
        # Format existing themes
        existing_formatted = []
        for theme in existing_themes:
            existing_formatted.append({
                "id": theme.get("id"),
                "name": theme.get("name"),
                "aliases": theme.get("aliases", []),
                "status": theme.get("status"),
                "description": theme.get("description")
            })

        # Wrap theme data for injection protection
        themes_data = (
            f"## Existing Themes\n{json.dumps(existing_formatted, indent=2)}\n\n"
            f"## New Themes to Match\n{json.dumps(new_themes, indent=2)}"
        )
        wrapped_themes = wrap_content_for_prompt(
            sanitize_content_text(themes_data), max_chars=30000
        )

        prompt = f"""Match new themes against existing themes.

{wrapped_themes}

---

For each new theme, determine:
1. Does it match an existing theme? (same concept, different wording)
2. Is it an evolution of an existing theme? (concept has developed/changed)
3. Should it be a new theme?
4. Should it potentially be merged with an existing theme? (suggest but don't auto-merge)

Respond with JSON:
{{
  "matches": [
    {{
      "new_theme_name": "name from new themes list",
      "action": "update" | "create" | "evolve",
      "match_id": existing theme ID or null,
      "is_evolution": true/false,
      "evolved_from_id": ID if evolution,
      "merge_suggestion": {{
        "target_id": ID,
        "reason": "why these might be the same"
      }} or null,
      "evidence_to_add": {{
        "source": "source name",
        "summary": "what this source said"
      }}
    }}
  ]
}}

Be conservative - only match if clearly the same concept.
If unsure, create a new theme and suggest merge."""

        return prompt


# Source weights for evidence strength mapping (from SynthesisAgent)
_SOURCE_WEIGHTS = {
    "42macro": 1.5,
    "discord": 1.5,
    "kt_technical": 1.2,
    "substack": 1.0,
    "youtube": 0.8,
}


def _evidence_strength_for_source(source_name: str) -> str:
    """Map source weight to evidence strength: >=1.5 -> strong, >=1.0 -> moderate, <1.0 -> weak."""
    weight = _SOURCE_WEIGHTS.get(source_name, 1.0)
    if weight >= 1.5:
        return "strong"
    elif weight >= 1.0:
        return "moderate"
    return "weak"


def _compute_conviction(source_names: List[str]) -> float:
    """Compute dynamic conviction from weighted source count: min(0.9, 0.3 + 0.15 * weighted_count)."""
    weighted_count = sum(_SOURCE_WEIGHTS.get(s, 1.0) for s in source_names)
    return min(0.9, 0.3 + 0.15 * weighted_count)


def extract_and_track_themes(
    synthesis_data: Dict[str, Any],
    db_session,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to extract themes from synthesis and update database.

    Args:
        synthesis_data: Full v3 synthesis JSON
        db_session: SQLAlchemy database session
        api_key: Optional Claude API key

    Returns:
        Summary of theme operations performed
    """
    from backend.models import Theme

    agent = ThemeExtractorAgent(api_key=api_key)

    # Extract themes from synthesis
    new_themes = agent.extract_themes_from_synthesis(synthesis_data)

    if not new_themes:
        return {"status": "no_themes", "extracted": 0, "created": 0, "updated": 0}

    # Get existing themes from database (include evolved to avoid re-creating them)
    existing_db_themes = db_session.query(Theme).filter(
        Theme.status.in_(["emerging", "active", "evolved"])
    ).all()

    existing_themes = []
    for theme in existing_db_themes:
        aliases = []
        if theme.aliases:
            try:
                aliases = json.loads(theme.aliases)
            except json.JSONDecodeError:
                pass

        existing_themes.append({
            "id": theme.id,
            "name": theme.name,
            "aliases": aliases,
            "status": theme.status,
            "description": theme.description
        })

    # Match themes
    matches = agent.match_themes(new_themes, existing_themes)

    # Process matches
    created = 0
    updated = 0
    now = datetime.utcnow()

    for match in matches:
        action = match.get("action")
        match_id = match.get("match_id")
        new_theme_data = match.get("new_theme", {})

        if action == "create":
            # Create new theme (or update if name already exists)
            theme_name = new_theme_data.get("name", "").strip()
            if not theme_name:
                logger.warning("Skipping theme with empty name")
                continue

            theme_sources = list(new_theme_data.get("sources", {}).keys())
            source_evidence = {}
            for source, view in new_theme_data.get("sources", {}).items():
                source_evidence[source] = [{
                    "date": now.strftime("%Y-%m-%d"),
                    "summary": view,
                    "strength": _evidence_strength_for_source(source)
                }]

            # Check if theme with this name already exists
            existing = db_session.query(Theme).filter(Theme.name == theme_name).first()
            if existing:
                # Update existing theme with new evidence
                evidence = json.loads(existing.source_evidence) if existing.source_evidence else {}
                for src, entries in source_evidence.items():
                    if src not in evidence:
                        evidence[src] = []
                    evidence[src].extend(entries)
                existing.source_evidence = json.dumps(evidence)
                existing.last_updated_at = now
                existing.evidence_count = sum(len(v) for v in evidence.values())
                existing.current_conviction = _compute_conviction(list(evidence.keys()))
                if existing.status == "emerging" and len(evidence) >= 2:
                    existing.status = "active"
                updated += 1
            else:
                theme = Theme(
                    name=theme_name,
                    description=new_theme_data.get("description"),
                    source_evidence=json.dumps(source_evidence),
                    catalysts=json.dumps(new_theme_data.get("catalysts", [])),
                    first_source=theme_sources[0] if theme_sources else None,
                    status=new_theme_data.get("status", "emerging"),
                    first_mentioned_at=now,
                    last_updated_at=now,
                    current_conviction=_compute_conviction(theme_sources),
                    evidence_count=len(source_evidence)
                )
                db_session.add(theme)
                created += 1

        elif action == "update" and match_id:
            # Update existing theme with new evidence
            theme = db_session.query(Theme).filter(Theme.id == match_id).first()
            if theme:
                # Parse existing evidence
                evidence = json.loads(theme.source_evidence) if theme.source_evidence else {}

                # Add new evidence
                evidence_to_add = match.get("evidence_to_add", {})
                source = evidence_to_add.get("source")
                if source:
                    if source not in evidence:
                        evidence[source] = []
                    evidence[source].append({
                        "date": now.strftime("%Y-%m-%d"),
                        "summary": evidence_to_add.get("summary", ""),
                        "strength": _evidence_strength_for_source(source)
                    })

                theme.source_evidence = json.dumps(evidence)
                theme.last_updated_at = now
                theme.evidence_count = sum(len(v) for v in evidence.values())
                theme.current_conviction = _compute_conviction(list(evidence.keys()))

                # Upgrade status if now has multiple sources
                if theme.status == "emerging" and len(evidence) >= 2:
                    theme.status = "active"

                updated += 1

        elif action == "evolve" and match.get("evolved_from_id"):
            # Create evolved theme (or update if name already exists)
            theme_name = new_theme_data.get("name", "").strip()
            if not theme_name:
                logger.warning("Skipping evolved theme with empty name")
                continue

            theme_sources = list(new_theme_data.get("sources", {}).keys())
            source_evidence = {}
            for source, view in new_theme_data.get("sources", {}).items():
                source_evidence[source] = [{
                    "date": now.strftime("%Y-%m-%d"),
                    "summary": view,
                    "strength": _evidence_strength_for_source(source)
                }]

            # Check if theme with this name already exists
            existing = db_session.query(Theme).filter(Theme.name == theme_name).first()
            if existing:
                evidence = json.loads(existing.source_evidence) if existing.source_evidence else {}
                for src, entries in source_evidence.items():
                    if src not in evidence:
                        evidence[src] = []
                    evidence[src].extend(entries)
                existing.source_evidence = json.dumps(evidence)
                existing.last_updated_at = now
                existing.evidence_count = sum(len(v) for v in evidence.values())
                existing.current_conviction = _compute_conviction(list(evidence.keys()))
                updated += 1
            else:
                theme = Theme(
                    name=theme_name,
                    description=new_theme_data.get("description"),
                    evolved_from_theme_id=match.get("evolved_from_id"),
                    source_evidence=json.dumps(source_evidence),
                    catalysts=json.dumps(new_theme_data.get("catalysts", [])),
                    first_source=theme_sources[0] if theme_sources else None,
                    status="active",
                    first_mentioned_at=now,
                    last_updated_at=now,
                    current_conviction=_compute_conviction(theme_sources),
                    evidence_count=len(source_evidence)
                )
                db_session.add(theme)

            # Mark parent as evolved
            parent = db_session.query(Theme).filter(Theme.id == match.get("evolved_from_id")).first()
            if parent:
                parent.status = "evolved"

            created += 1

    db_session.commit()

    return {
        "status": "success",
        "extracted": len(new_themes),
        "created": created,
        "updated": updated,
        "matches": matches
    }
