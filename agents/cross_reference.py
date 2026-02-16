"""
Cross-Reference Agent

Finds confluence patterns across multiple sources and performs Bayesian conviction updating.
Identifies when 2+ independent sources align on same thesis, tracks conviction evolution.

Key Capabilities:
- Theme clustering across sources
- Cross-source confluence detection
- Bayesian conviction updating over time
- Contradiction detection
- High-conviction idea extraction

Bayesian Formula:
P(theme | new_evidence) = P(new_evidence | theme) * P(theme) / P(new_evidence)

Where:
- P(theme) = prior conviction
- P(new_evidence | theme) = evidence strength (from confluence score)
- P(new_evidence) = normalization constant
"""

import os
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from agents.base_agent import BaseAgent
from backend.utils.sanitization import wrap_content_for_prompt, sanitize_content_text

logger = logging.getLogger(__name__)


class CrossReferenceAgent(BaseAgent):
    """
    Agent for finding confluence patterns and tracking conviction evolution.

    Pipeline:
    1. Take multiple confluence-scored analyses
    2. Extract and cluster themes
    3. Find cross-source confluence (2+ sources on same theme)
    4. Detect contradictions
    5. Perform Bayesian updating
    6. Output high-conviction ideas
    """

    # Similarity threshold for theme clustering (0-1)
    THEME_SIMILARITY_THRESHOLD = 0.7

    # Minimum sources required for strong confluence
    MIN_SOURCES_FOR_CONFLUENCE = 2

    # Bayesian prior conviction (starting point for new themes)
    DEFAULT_PRIOR_CONVICTION = 0.3

    # Evidence reliability weights by source quality
    SOURCE_RELIABILITY = {
        "42macro": 0.9,
        "discord": 0.85,
        "kt_technical": 0.8,
        "twitter": 0.7,
        "youtube": 0.75,
        "substack": 0.75
    }

    # Conviction buckets for qualitative mapping
    # Maps raw Bayesian probabilities to human-readable confidence levels
    # Prevents false precision from displaying raw percentages
    CONVICTION_BUCKETS = {
        "low": (0.0, 0.45),           # Low conviction: <45%
        "medium": (0.45, 0.65),       # Medium conviction: 45-65%
        "high": (0.65, 0.85),         # High conviction: 65-85%
        "table_pounding": (0.85, 1.0) # Table pounding: >85%
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize Cross-Reference Agent.

        Args:
            api_key: Claude API key (defaults to env var)
            model: Claude model to use
        """
        super().__init__(api_key=api_key, model=model)
        logger.info(f"Initialized CrossReferenceAgent")

    def analyze(
        self,
        confluence_scores: List[Dict[str, Any]],
        time_window_days: int = 7,
        min_sources: int = 2,
        historical_themes: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Find confluence patterns and update conviction across sources.

        Args:
            confluence_scores: List of confluence-scored analyses
            time_window_days: Time window for analysis (days)
            min_sources: Minimum sources required for confluence
            historical_themes: Previous theme tracking data for Bayesian updates

        Returns:
            Cross-reference analysis with confluent themes and contradictions
        """
        if historical_themes is None:
            historical_themes = []

        # Graceful handling for empty scores
        if not confluence_scores:
            logger.warning("No confluence scores provided for cross-reference analysis")
            return {
                "confluent_themes": [],
                "contradictions": [],
                "high_conviction_ideas": [],
                "total_themes": 0,
                "clustered_themes_count": 0,
                "confluent_count": 0,
                "contradiction_count": 0,
                "high_conviction_count": 0,
                "time_window_days": time_window_days,
                "sources_analyzed": 0,
                "analyzed_at": datetime.utcnow().isoformat()
            }

        try:
            logger.info(
                f"Cross-referencing {len(confluence_scores)} analyses "
                f"(window: {time_window_days}d, min sources: {min_sources})"
            )

            # Step 1: Extract themes from all analyses
            all_themes = self._extract_themes(confluence_scores)

            # Step 2: Cluster similar themes using Claude
            clustered_themes = self.cluster_themes(all_themes)

            # Step 3: Find confluent themes (2+ sources agree)
            confluent_themes = self._find_confluent_themes(
                clustered_themes,
                min_sources=min_sources
            )

            # Step 4: Perform Bayesian updates
            updated_themes = self._bayesian_update_themes(
                confluent_themes,
                historical_themes
            )

            # Step 5: Detect contradictions
            contradictions = self._detect_contradictions(confluence_scores)

            # Step 6: Extract high-conviction ideas
            high_conviction_ideas = self._extract_high_conviction(updated_themes)

            # Build result
            result = {
                "confluent_themes": updated_themes,
                "contradictions": contradictions,
                "high_conviction_ideas": high_conviction_ideas,
                "total_themes": len(all_themes),
                "clustered_themes_count": len(clustered_themes),
                "confluent_count": len(updated_themes),
                "contradiction_count": len(contradictions),
                "high_conviction_count": len(high_conviction_ideas),
                "time_window_days": time_window_days,
                "sources_analyzed": len(set(score.get("content_source", "unknown")
                                           for score in confluence_scores)),
                "analyzed_at": datetime.utcnow().isoformat()
            }

            logger.info(
                f"Cross-reference complete. "
                f"Found {len(updated_themes)} confluent themes, "
                f"{len(contradictions)} contradictions, "
                f"{len(high_conviction_ideas)} high-conviction ideas"
            )

            return result

        except Exception as e:
            logger.error(f"Cross-reference analysis failed: {e}")
            raise

    def _extract_themes(
        self,
        confluence_scores: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract all themes from confluence-scored analyses.

        Args:
            confluence_scores: Confluence scores

        Returns:
            List of extracted themes with metadata
        """
        themes = []

        for score in confluence_scores:
            # Get primary thesis
            primary_thesis = score.get("primary_thesis", "")

            # Get source and date
            source = score.get("content_source", "unknown")
            scored_at = score.get("scored_at", datetime.utcnow().isoformat())

            # Get key metrics
            core_total = score.get("core_total", 0)
            total_score = score.get("total_score", 0)
            meets_threshold = score.get("meets_threshold", False)
            confluence_level = score.get("confluence_level", "weak")

            # Get additional context
            variant_view = score.get("variant_view", "")
            p_and_l_mechanism = score.get("p_and_l_mechanism", "")
            falsification_criteria = score.get("falsification_criteria", [])

            if primary_thesis:
                theme = {
                    "theme": primary_thesis,
                    "source": source,
                    "date": scored_at,
                    "core_score": core_total,
                    "total_score": total_score,
                    "meets_threshold": meets_threshold,
                    "confluence_level": confluence_level,
                    "variant_view": variant_view,
                    "p_and_l_mechanism": p_and_l_mechanism,
                    "falsification_criteria": falsification_criteria,
                    "full_analysis": score
                }
                themes.append(theme)

        logger.info(f"Extracted {len(themes)} themes from {len(confluence_scores)} analyses")
        return themes

    def cluster_themes(
        self,
        themes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Cluster similar themes using Claude for semantic similarity.

        Args:
            themes: List of themes to cluster

        Returns:
            Clustered themes
        """
        if not themes:
            return []

        try:
            logger.info(f"Clustering {len(themes)} themes")

            # Build prompt for Claude
            system_prompt = """You are analyzing investment themes to find similar ideas across different sources.

Your job is to cluster themes that are essentially the same investment thesis, even if worded differently.

For example:
- "Tech sector outperformance likely" and "NASDAQ to outperform S&P" = SAME theme
- "Fed pause imminent" and "Central bank to hold rates" = SAME theme
- "Tech rotation" and "Energy sector strength" = DIFFERENT themes

Be smart about semantic similarity."""

            themes_text = "\n".join([
                f"{i+1}. [{theme['source']}] {theme['theme']} (score: {theme['core_score']}/10)"
                for i, theme in enumerate(themes)
            ])
            wrapped_themes = wrap_content_for_prompt(
                sanitize_content_text(themes_text), max_chars=30000
            )

            user_prompt = f"""Cluster these investment themes by similarity:

{wrapped_themes}

Return a JSON array of clusters, where each cluster contains theme indices that are similar:

{{
    "clusters": [
        {{
            "cluster_id": 1,
            "representative_theme": "Main theme description",
            "theme_indices": [1, 3, 5],
            "confidence": 0.85
        }},
        ...
    ]
}}

Rules:
- Themes must be semantically similar (same investment idea)
- Different instruments on same theme = SAME cluster
- Opposite views = DIFFERENT clusters
- Be conservative - only cluster if truly similar

Return ONLY valid JSON."""

            # Call Claude
            response = self.call_claude(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.0,
                expect_json=True
            )

            clusters_data = response.get("clusters", [])

            # Build clustered themes
            clustered = []
            for cluster in clusters_data:
                indices = cluster.get("theme_indices", [])
                if not indices:
                    continue

                # Get themes in this cluster (adjust for 0-based indexing)
                cluster_themes = [themes[i-1] for i in indices if 0 < i <= len(themes)]

                if cluster_themes:
                    clustered.append({
                        "representative_theme": cluster.get("representative_theme", ""),
                        "themes": cluster_themes,
                        "confidence": cluster.get("confidence", 0.0),
                        "source_count": len(set(t["source"] for t in cluster_themes))
                    })

            logger.info(f"Clustered into {len(clustered)} groups")
            return clustered

        except Exception as e:
            logger.warning(f"Theme clustering failed, returning unclustered: {e}")
            # Fallback: each theme is its own cluster
            return [{"representative_theme": t["theme"], "themes": [t], "confidence": 1.0, "source_count": 1}
                    for t in themes]

    def _find_confluent_themes(
        self,
        clustered_themes: List[Dict[str, Any]],
        min_sources: int
    ) -> List[Dict[str, Any]]:
        """
        Find themes with cross-source confluence.

        Args:
            clustered_themes: Clustered themes
            min_sources: Minimum sources required

        Returns:
            Confluent themes
        """
        confluent = []

        for cluster in clustered_themes:
            source_count = cluster.get("source_count", 0)

            if source_count >= min_sources:
                themes = cluster["themes"]

                # Calculate aggregate metrics
                avg_core_score = sum(t["core_score"] for t in themes) / len(themes)
                avg_total_score = sum(t["total_score"] for t in themes) / len(themes)

                # Get all sources
                supporting_sources = [
                    {
                        "source": t["source"],
                        "date": t["date"],
                        "score": t["core_score"],
                        "meets_threshold": t["meets_threshold"]
                    }
                    for t in themes
                ]

                # Find earliest mention
                dates = [datetime.fromisoformat(t["date"].replace('Z', '+00:00'))
                        for t in themes if t.get("date")]
                first_mentioned = min(dates).isoformat() if dates else None

                confluent.append({
                    "theme": cluster["representative_theme"],
                    "supporting_sources": supporting_sources,
                    "evidence_count": len(themes),
                    "source_count": source_count,
                    "avg_core_score": round(avg_core_score, 1),
                    "avg_total_score": round(avg_total_score, 1),
                    "first_mentioned": first_mentioned,
                    "cluster_confidence": cluster.get("confidence", 0.0),
                    "themes_detail": themes
                })

        return confluent

    def _bayesian_update_themes(
        self,
        confluent_themes: List[Dict[str, Any]],
        historical_themes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Perform Bayesian updates on conviction for confluent themes.

        Args:
            confluent_themes: Current confluent themes
            historical_themes: Historical theme data

        Returns:
            Updated themes with Bayesian conviction
        """
        updated = []

        # Build historical lookup
        historical_map = {h["theme"]: h for h in historical_themes}

        for theme in confluent_themes:
            theme_text = theme["theme"]

            # Get prior conviction
            historical = historical_map.get(theme_text, {})
            prior_conviction = historical.get("current_conviction", self.DEFAULT_PRIOR_CONVICTION)

            # Calculate evidence strength from core scores
            avg_core_score = theme["avg_core_score"]
            evidence_strength = min(avg_core_score / 10.0, 1.0)  # Normalize to 0-1

            # Get source reliability (average across sources)
            sources = [s["source"] for s in theme["supporting_sources"]]
            source_reliabilities = [self.SOURCE_RELIABILITY.get(s, 0.75) for s in sources]
            avg_reliability = sum(source_reliabilities) / len(source_reliabilities) if source_reliabilities else 0.75

            # Perform Bayesian update
            posterior_conviction = self._bayesian_update(
                prior_conviction,
                evidence_strength,
                avg_reliability
            )

            # Calculate confidence interval (simple approximation)
            confidence_interval = [
                max(0.0, posterior_conviction - 0.1),
                min(1.0, posterior_conviction + 0.1)
            ]

            # Build conviction history
            conviction_history = historical.get("conviction_history", [])
            conviction_history.append({
                "date": datetime.utcnow().isoformat(),
                "conviction": round(posterior_conviction, 3)
            })

            # Map conviction to qualitative bucket (prevents false precision)
            conviction_bucket = self._map_conviction_to_bucket(posterior_conviction)

            # Update theme
            theme["current_conviction"] = round(posterior_conviction, 3)
            theme["prior_conviction"] = round(prior_conviction, 3)
            theme["conviction_bucket"] = conviction_bucket  # Qualitative label for UI
            theme["confidence_interval"] = [round(c, 3) for c in confidence_interval]
            theme["conviction_history"] = conviction_history[-10:]  # Keep last 10
            theme["evidence_strength"] = round(evidence_strength, 3)
            theme["source_reliability"] = round(avg_reliability, 3)

            updated.append(theme)

        return updated

    def _bayesian_update(
        self,
        prior: float,
        evidence_strength: float,
        evidence_reliability: float
    ) -> float:
        """
        Perform Bayesian update on conviction.

        Formula: P(H|E) = P(E|H) * P(H) / P(E)

        Args:
            prior: Prior conviction (0-1)
            evidence_strength: Strength of new evidence (0-1)
            evidence_reliability: Reliability of evidence source (0-1)

        Returns:
            Posterior conviction (0-1)
        """
        # Likelihood: P(E|H) = evidence strength weighted by reliability
        likelihood = evidence_strength * evidence_reliability

        # Posterior using Bayes rule with normalization
        numerator = likelihood * prior
        denominator = numerator + (1 - likelihood) * (1 - prior)

        if denominator == 0:
            return prior

        posterior = numerator / denominator

        # Ensure bounds
        return max(0.0, min(1.0, posterior))

    def _map_conviction_to_bucket(self, conviction: float) -> str:
        """
        Map raw Bayesian conviction probability to qualitative bucket.

        This prevents false precision - a 0.73 conviction is displayed as "high"
        rather than "73%" which implies unwarranted mathematical certainty.

        Trust the trend of the number, not the absolute value.

        Args:
            conviction: Raw conviction probability (0.0 - 1.0)

        Returns:
            Qualitative bucket: "low", "medium", "high", or "table_pounding"
        """
        for bucket_name, (min_val, max_val) in self.CONVICTION_BUCKETS.items():
            if min_val <= conviction < max_val:
                return bucket_name

        # Fallback for exactly 1.0
        return "table_pounding"

    def _detect_contradictions(
        self,
        confluence_scores: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect contradictions between sources.

        Args:
            confluence_scores: Confluence scores

        Returns:
            List of contradictions
        """
        contradictions = []

        # Group by similar themes, look for opposing views
        # For now, use a simple heuristic based on sentiment and variant_view

        by_ticker = defaultdict(list)

        for score in confluence_scores:
            # Get tickers from original analysis
            tickers = []
            if "full_analysis" in score:
                tickers = score["full_analysis"].get("tickers_mentioned", []) or []

            variant_view = score.get("variant_view", "")
            sentiment = "unknown"

            # Try to infer sentiment from variant view
            if variant_view:
                if any(word in variant_view.lower() for word in ["bullish", "upside", "outperform", "buy"]):
                    sentiment = "bullish"
                elif any(word in variant_view.lower() for word in ["bearish", "downside", "underperform", "sell"]):
                    sentiment = "bearish"

            for ticker in tickers[:3]:  # Limit to avoid too many
                by_ticker[ticker].append({
                    "source": score.get("content_source", "unknown"),
                    "sentiment": sentiment,
                    "view": variant_view,
                    "score": score
                })

        # Find opposing views on same ticker
        for ticker, views in by_ticker.items():
            if len(views) < 2:
                continue

            bullish = [v for v in views if v["sentiment"] == "bullish"]
            bearish = [v for v in views if v["sentiment"] == "bearish"]

            if bullish and bearish:
                contradictions.append({
                    "ticker": ticker,
                    "conflicting_views": len(bullish) + len(bearish),
                    "bullish_sources": [{"source": v["source"], "view": v["view"][:100]} for v in bullish],
                    "bearish_sources": [{"source": v["source"], "view": v["view"][:100]} for v in bearish]
                })

        return contradictions

    def _extract_high_conviction(
        self,
        themes: List[Dict[str, Any]],
        conviction_threshold: float = 0.75,
        min_sources: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Extract high-conviction ideas.

        Args:
            themes: Updated themes with conviction
            conviction_threshold: Minimum conviction (0-1)
            min_sources: Minimum sources

        Returns:
            High-conviction ideas
        """
        high_conviction = []

        for theme in themes:
            conviction = theme.get("current_conviction", 0.0)
            source_count = theme.get("source_count", 0)

            if conviction >= conviction_threshold and source_count >= min_sources:
                high_conviction.append({
                    "theme": theme["theme"],
                    "conviction": conviction,
                    "sources": [s["source"] for s in theme["supporting_sources"]],
                    "evidence_count": theme["evidence_count"],
                    "avg_score": theme["avg_core_score"],
                    "first_mentioned": theme.get("first_mentioned"),
                    "conviction_trend": self._calculate_trend(theme.get("conviction_history", []))
                })

        # Sort by conviction descending
        high_conviction.sort(key=lambda x: x["conviction"], reverse=True)

        return high_conviction

    def _calculate_trend(self, conviction_history: List[Dict[str, Any]]) -> str:
        """
        Calculate conviction trend from history.

        Args:
            conviction_history: List of conviction measurements

        Returns:
            Trend description
        """
        if len(conviction_history) < 2:
            return "new"

        convictions = [h["conviction"] for h in conviction_history]

        # Simple trend: compare first and last
        first = convictions[0]
        last = convictions[-1]

        diff = last - first

        if diff > 0.1:
            return "rising"
        elif diff < -0.1:
            return "falling"
        else:
            return "stable"
