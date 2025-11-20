"""
Transcript-Chart Matcher

Matches video transcript mentions to PDF chart images for optimized analysis.
Reduces cost by only analyzing charts that are actually discussed in the video.

Use case: 42 Macro videos discuss ~10-15 of 70-80 PDF slides
Cost reduction: 85% (from $0.40 to $0.06 per video)
"""

import logging
import re
from typing import Dict, Any, List, Optional
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class TranscriptChartMatcher:
    """
    Matches chart mentions in video transcripts to PDF images.

    Used to prioritize which charts to analyze based on what's discussed.
    """

    # Common patterns for chart mentions in transcripts
    CHART_PATTERNS = [
        r"looking at (?:the )?([^,.]+?)(?:chart|data|graph|slide)",
        r"this (?:chart|graph|slide) shows ([^,.]+)",
        r"(?:the )?([A-Z][^\.,]+?) (?:chart|data|is showing)",
        r"on (?:the )?([^,.]+?) (?:chart|slide|page)",
        r"(?:let's|we'll) look at ([^,.]+?)(?:here|now|next|\.|,)",
        r"moving (?:on )?to (?:the )?([^,.]+?)(?:chart|data|slide)",
        r"(?:here's|here is) (?:the )?([^,.]+?)(?:chart|data)",
    ]

    # Keywords that indicate a chart discussion
    CHART_KEYWORDS = [
        "chart", "graph", "slide", "data", "showing", "looking at",
        "moving to", "next up", "this shows", "we see", "you can see"
    ]

    # Common asset/topic names to look for
    ASSET_PATTERNS = [
        r"\b(?:SPX|S&P 500|S&P|SPY)\b",
        r"\b(?:QQQ|NASDAQ|NDX)\b",
        r"\b(?:DXY|dollar|USD)\b",
        r"\b(?:VIX|volatility|vol)\b",
        r"\b(?:TLT|bonds|treasuries|yields)\b",
        r"\b(?:GLD|gold|commodities)\b",
        r"\b(?:BTC|bitcoin|crypto|ETH|ethereum)\b",
        r"\b(?:CPI|inflation|PCE)\b",
        r"\b(?:GDP|growth|employment|jobs)\b",
        r"\b(?:Fed|FOMC|rates|policy)\b",
    ]

    def __init__(self):
        """Initialize the matcher."""
        logger.info("Initialized TranscriptChartMatcher")

    def extract_chart_mentions(self, transcript: str) -> List[Dict[str, Any]]:
        """
        Extract chart mentions from video transcript.

        Args:
            transcript: Full video transcript text

        Returns:
            List of chart mentions with metadata
        """
        try:
            logger.info(f"Extracting chart mentions from transcript ({len(transcript)} chars)")

            mentions = []

            # Split transcript into segments (by sentence or time if available)
            segments = self._segment_transcript(transcript)

            for i, segment in enumerate(segments):
                segment_lower = segment.lower()

                # Check if this segment discusses a chart
                has_chart_keyword = any(kw in segment_lower for kw in self.CHART_KEYWORDS)

                if has_chart_keyword:
                    # Extract what chart is being discussed
                    chart_topics = self._extract_topics(segment)

                    if chart_topics:
                        mentions.append({
                            "segment_index": i,
                            "topics": chart_topics,
                            "text_snippet": segment[:200],  # First 200 chars
                            "confidence": self._calculate_confidence(segment)
                        })

            logger.info(f"Found {len(mentions)} chart mentions")
            return mentions

        except Exception as e:
            logger.error(f"Failed to extract chart mentions: {e}")
            return []

    def _segment_transcript(self, transcript: str) -> List[str]:
        """
        Split transcript into segments for analysis.

        Args:
            transcript: Full transcript

        Returns:
            List of transcript segments
        """
        # Simple sentence-based segmentation
        # Could be enhanced with timestamp-based segmentation if available
        sentences = re.split(r'[.!?]+', transcript)
        return [s.strip() for s in sentences if s.strip()]

    def _extract_topics(self, text: str) -> List[str]:
        """
        Extract chart topics from text segment.

        Args:
            text: Text segment

        Returns:
            List of extracted topics
        """
        topics = []

        # Try pattern matching first
        for pattern in self.CHART_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                topic = match.group(1).strip()
                if topic and len(topic) > 3:  # Ignore very short matches
                    topics.append(topic)

        # Also look for specific assets
        for pattern in self.ASSET_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                asset = match.group(0).strip()
                topics.append(asset)

        # Deduplicate and clean
        topics = list(set([t.lower() for t in topics]))

        return topics

    def _calculate_confidence(self, text: str) -> float:
        """
        Calculate confidence score for a chart mention.

        Args:
            text: Text segment

        Returns:
            Confidence score 0.0-1.0
        """
        confidence = 0.5  # Base confidence

        text_lower = text.lower()

        # Boost confidence for explicit chart mentions
        if "looking at" in text_lower or "this chart" in text_lower:
            confidence += 0.3

        # Boost for multiple chart keywords
        keyword_count = sum(1 for kw in self.CHART_KEYWORDS if kw in text_lower)
        confidence += min(keyword_count * 0.1, 0.2)

        return min(confidence, 1.0)

    def match_to_images(
        self,
        chart_mentions: List[Dict[str, Any]],
        image_metadata: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Match chart mentions to PDF image metadata.

        Args:
            chart_mentions: List of extracted chart mentions
            image_metadata: List of image metadata from PDF extraction

        Returns:
            Prioritized list of images to analyze
        """
        try:
            logger.info(
                f"Matching {len(chart_mentions)} mentions to {len(image_metadata)} images"
            )

            prioritized_images = []

            # Create topic list from all mentions
            all_topics = []
            for mention in chart_mentions:
                all_topics.extend(mention["topics"])

            # Deduplicate topics
            unique_topics = list(set([t.lower() for t in all_topics]))
            logger.info(f"Unique topics mentioned: {unique_topics}")

            # Match topics to images
            for image in image_metadata:
                image_path = image.get("image_path", "")
                page_number = image.get("page_number", 0)

                # Calculate match score for this image
                match_score = 0.0

                # Simple filename matching
                image_filename = image_path.lower()
                for topic in unique_topics:
                    if topic in image_filename:
                        match_score += 0.5

                # If we have extracted text from the image (future enhancement)
                # we could match against that too

                if match_score > 0:
                    prioritized_images.append({
                        "image_metadata": image,
                        "match_score": match_score,
                        "matched_topics": [t for t in unique_topics if t in image_filename],
                        "priority": "high" if match_score >= 0.5 else "medium"
                    })

            # Sort by match score (highest first)
            prioritized_images.sort(key=lambda x: x["match_score"], reverse=True)

            logger.info(
                f"Matched {len(prioritized_images)} images "
                f"(high priority: {sum(1 for i in prioritized_images if i['priority'] == 'high')})"
            )

            return prioritized_images

        except Exception as e:
            logger.error(f"Failed to match images: {e}")
            return []

    def prioritize_for_analysis(
        self,
        transcript: str,
        all_images: List[Dict[str, Any]],
        max_analyze: int = 15
    ) -> Dict[str, Any]:
        """
        Complete pipeline: Extract mentions → Match → Prioritize.

        Args:
            transcript: Video transcript
            all_images: All extracted PDF images
            max_analyze: Maximum number of images to analyze

        Returns:
            Prioritization results with images to analyze
        """
        try:
            logger.info("=" * 80)
            logger.info("TRANSCRIPT-CHART MATCHING PIPELINE")
            logger.info("=" * 80)
            logger.info(f"Transcript length: {len(transcript)} chars")
            logger.info(f"Total images: {len(all_images)}")
            logger.info(f"Max to analyze: {max_analyze}")

            # Step 1: Extract chart mentions from transcript
            chart_mentions = self.extract_chart_mentions(transcript)

            if not chart_mentions:
                logger.warning("No chart mentions found in transcript - analyzing all images")
                return {
                    "status": "no_mentions",
                    "images_to_analyze": all_images[:max_analyze],
                    "fallback_reason": "No chart mentions detected"
                }

            # Step 2: Match mentions to images
            matched_images = self.match_to_images(chart_mentions, all_images)

            if not matched_images:
                logger.warning("No matches found - analyzing first N images")
                return {
                    "status": "no_matches",
                    "images_to_analyze": all_images[:max_analyze],
                    "chart_mentions": chart_mentions,
                    "fallback_reason": "Chart mentions found but no matches"
                }

            # Step 3: Prioritize matched images
            high_priority = [img for img in matched_images if img["priority"] == "high"]
            medium_priority = [img for img in matched_images if img["priority"] == "medium"]

            # Take high priority first, then medium until we hit max
            images_to_analyze = (high_priority + medium_priority)[:max_analyze]

            # If we still have room, add some unmatched images
            matched_paths = set(img["image_metadata"]["image_path"] for img in images_to_analyze)
            unmatched = [img for img in all_images if img["image_path"] not in matched_paths]
            remaining_slots = max_analyze - len(images_to_analyze)
            if remaining_slots > 0:
                images_to_analyze.extend(
                    [{"image_metadata": img, "priority": "low"} for img in unmatched[:remaining_slots]]
                )

            logger.info("=" * 80)
            logger.info("PRIORITIZATION COMPLETE")
            logger.info("=" * 80)
            logger.info(f"Chart mentions found: {len(chart_mentions)}")
            logger.info(f"Matched images: {len(matched_images)}")
            logger.info(f"High priority: {len(high_priority)}")
            logger.info(f"Medium priority: {len(medium_priority)}")
            logger.info(f"Images to analyze: {len(images_to_analyze)}/{len(all_images)}")
            logger.info(f"Cost reduction: {(1 - len(images_to_analyze)/len(all_images))*100:.1f}%")

            return {
                "status": "success",
                "chart_mentions": chart_mentions,
                "matched_images": matched_images,
                "images_to_analyze": [img["image_metadata"] for img in images_to_analyze],
                "cost_reduction_pct": (1 - len(images_to_analyze)/len(all_images)) * 100,
                "high_priority_count": len(high_priority),
                "medium_priority_count": len(medium_priority)
            }

        except Exception as e:
            logger.error(f"Prioritization pipeline failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "images_to_analyze": all_images[:max_analyze],  # Fallback
                "fallback_reason": f"Error: {str(e)}"
            }
