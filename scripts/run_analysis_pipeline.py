"""
Analysis Pipeline Orchestrator

Runs the complete AI analysis pipeline on collected content:
1. Content Classifier - Routes content to appropriate analyzer
2. Specialized Analyzers - PDF, Image, Transcript based on content type
3. Confluence Scorer - Scores content against 7-pillar framework
4. Cross-Reference Agent - Finds themes and confluence across sources

Usage:
    python scripts/run_analysis_pipeline.py --limit 10  # Process 10 items
    python scripts/run_analysis_pipeline.py --all       # Process all unprocessed
"""

import sys
import os
import argparse
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.content_classifier import ContentClassifierAgent
from agents.pdf_analyzer import PDFAnalyzerAgent
from agents.image_intelligence import ImageIntelligenceAgent
from agents.transcript_harvester import TranscriptHarvesterAgent
from agents.confluence_scorer import ConfluenceScorerAgent
from agents.cross_reference import CrossReferenceAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """
    Orchestrates the complete analysis pipeline for collected content.
    """

    def __init__(self):
        """Initialize all agents."""
        logger.info("Initializing analysis pipeline agents...")

        self.classifier = ContentClassifierAgent()
        self.pdf_analyzer = PDFAnalyzerAgent()
        self.image_analyzer = ImageIntelligenceAgent()
        self.transcript_harvester = TranscriptHarvesterAgent()
        self.confluence_scorer = ConfluenceScorerAgent()
        self.cross_reference = CrossReferenceAgent()

        logger.info("All agents initialized successfully")

    async def analyze_content(self, content_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run complete analysis pipeline on a single content item.

        Args:
            content_item: Raw content dictionary

        Returns:
            Complete analysis results
        """
        results = {
            "raw_content_id": content_item.get("id"),
            "source": content_item.get("source"),
            "status": "processing",
            "steps": {}
        }

        try:
            # Step 1: Classify content
            logger.info(f"[{results['raw_content_id']}] Step 1: Classifying content...")
            classification = self.classifier.classify(content_item)
            results["steps"]["classification"] = classification

            # Step 2: Route to appropriate analyzer
            content_type = content_item.get("content_type", "")
            route_to = classification.get("route_to_agents", [])

            analyzed_content = None

            # Handle PDFs
            if "pdf_analyzer" in route_to or content_type == "pdf":
                logger.info(f"[{results['raw_content_id']}] Step 2: Analyzing PDF...")
                if content_item.get("file_path"):
                    analyzed_content = await self.pdf_analyzer.analyze(content_item["file_path"])
                    results["steps"]["pdf_analysis"] = analyzed_content

            # Handle Images
            elif "image_intelligence" in route_to or content_type in ["image", "chart"]:
                logger.info(f"[{results['raw_content_id']}] Step 2: Analyzing image...")
                if content_item.get("file_path"):
                    analyzed_content = await self.image_analyzer.analyze(content_item["file_path"])
                    results["steps"]["image_analysis"] = analyzed_content

            # Handle Videos (transcripts)
            elif "transcript_harvester" in route_to or content_type == "video":
                logger.info(f"[{results['raw_content_id']}] Step 2: Harvesting video transcript...")
                if content_item.get("url"):
                    analyzed_content = await self.transcript_harvester.harvest(content_item["url"])
                    results["steps"]["transcript"] = analyzed_content

            # Handle text content
            elif content_type in ["text", "article", "tweet"]:
                logger.info(f"[{results['raw_content_id']}] Step 2: Using raw text...")
                # Text content goes straight to confluence scorer
                analyzed_content = {
                    "content_text": content_item.get("content_text", ""),
                    "source": content_item.get("source"),
                    "metadata": content_item.get("metadata", {})
                }
                results["steps"]["text_analysis"] = "passed_through"

            # Step 3: Score for confluence (if we have analyzed content)
            if analyzed_content:
                logger.info(f"[{results['raw_content_id']}] Step 3: Scoring confluence...")

                # Prepare content for scoring
                scoring_input = {
                    "source": content_item.get("source"),
                    "content_type": content_type,
                    "analyzed_content": analyzed_content,
                    "raw_content": content_item.get("content_text", "")
                }

                confluence_score = await self.confluence_scorer.score(scoring_input)
                results["steps"]["confluence_score"] = confluence_score

                logger.info(
                    f"[{results['raw_content_id']}] Confluence score: "
                    f"{confluence_score.get('total_score', 0)}/14 "
                    f"({confluence_score.get('conviction_tier', 'unknown')})"
                )

            results["status"] = "completed"
            logger.info(f"[{results['raw_content_id']}] ✅ Analysis pipeline complete")

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            logger.error(f"[{results['raw_content_id']}] ❌ Analysis failed: {e}")

        return results

    async def run_batch(self, content_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run analysis pipeline on multiple content items.

        Args:
            content_items: List of raw content dictionaries

        Returns:
            Batch processing results
        """
        logger.info("=" * 80)
        logger.info(f"Starting batch analysis of {len(content_items)} items")
        logger.info("=" * 80)

        results = {
            "total": len(content_items),
            "successful": 0,
            "failed": 0,
            "items": []
        }

        for i, content_item in enumerate(content_items, 1):
            logger.info(f"\nProcessing item {i}/{len(content_items)}")

            result = await self.analyze_content(content_item)
            results["items"].append(result)

            if result["status"] == "completed":
                results["successful"] += 1
            else:
                results["failed"] += 1

        # Step 4: Run cross-reference on all scored content
        logger.info("\n" + "=" * 80)
        logger.info("Step 4: Running cross-reference analysis...")
        logger.info("=" * 80)

        try:
            # Collect all confluence-scored items
            scored_items = []
            for result in results["items"]:
                if "confluence_score" in result.get("steps", {}):
                    scored_items.append(result["steps"]["confluence_score"])

            if scored_items:
                cross_ref_results = await self.cross_reference.analyze(scored_items)
                results["cross_reference"] = cross_ref_results

                logger.info(
                    f"✅ Cross-reference complete: "
                    f"{len(cross_ref_results.get('confluent_themes', []))} themes found"
                )
            else:
                logger.warning("No scored content available for cross-reference")
                results["cross_reference"] = {"message": "No scored content to analyze"}

        except Exception as e:
            logger.error(f"Cross-reference failed: {e}")
            results["cross_reference"] = {"error": str(e)}

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("ANALYSIS PIPELINE COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total items: {results['total']}")
        logger.info(f"Successful: {results['successful']}")
        logger.info(f"Failed: {results['failed']}")
        logger.info("=" * 80)

        return results


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run analysis pipeline on collected content")
    parser.add_argument("--limit", type=int, default=10, help="Number of items to process (default: 10)")
    parser.add_argument("--all", action="store_true", help="Process all unprocessed items")
    parser.add_argument("--source", type=str, help="Only process items from specific source")

    args = parser.parse_args()

    # For now, create mock data since we need database integration
    # In production, this would fetch from database
    logger.warning("=" * 80)
    logger.warning("NOTE: This is a dry-run demonstration")
    logger.warning("Database integration needed for production use")
    logger.warning("=" * 80)

    # Mock content items for demonstration
    mock_items = [
        {
            "id": 1,
            "source": "youtube",
            "content_type": "video",
            "url": "https://youtube.com/watch?v=example",
            "content_text": "Sample video about macro trends",
            "metadata": {}
        },
        {
            "id": 2,
            "source": "42macro",
            "content_type": "pdf",
            "file_path": "downloads/42macro/sample.pdf",
            "content_text": "",
            "metadata": {}
        }
    ]

    # Limit items if specified
    if not args.all:
        mock_items = mock_items[:args.limit]

    # Initialize pipeline
    pipeline = AnalysisPipeline()

    # Run analysis
    results = await pipeline.run_batch(mock_items)

    # Display summary
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print(f"Processed: {results['successful']}/{results['total']} items successfully")

    if results.get("cross_reference"):
        themes = results["cross_reference"].get("confluent_themes", [])
        print(f"Themes identified: {len(themes)}")
        if themes:
            print("\nTop Themes:")
            for theme in themes[:3]:
                print(f"  - {theme.get('theme', 'Unknown')}")
                print(f"    Sources: {len(theme.get('supporting_sources', []))}")
                print(f"    Confidence: {theme.get('confidence', 0):.2f}")


if __name__ == "__main__":
    asyncio.run(main())
