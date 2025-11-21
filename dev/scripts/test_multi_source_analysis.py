"""
Test Multi-Source Analysis

Demonstrates Chart Intelligence System analyzing PDFs from multiple sources:
- 42 Macro: Around The Horn (70-80 slides)
- Discord: Crypto Options Weekly (2-4 pages of charts)

Shows end-to-end: Extract → Classify → Analyze → Combine insights
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.pdf_analyzer import PDFAnalyzerAgent
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def analyze_pdf(pdf_path: str, source: str, label: str):
    """Analyze a single PDF and display results."""

    logger.info("=" * 80)
    logger.info(f"{label}")
    logger.info("=" * 80)
    logger.info(f"PDF: {Path(pdf_path).name}")
    logger.info(f"Source: {source}")
    logger.info("")

    if not os.path.exists(pdf_path):
        logger.error(f"PDF not found: {pdf_path}")
        return None

    # Initialize analyzer
    analyzer = PDFAnalyzerAgent()

    # Analyze with Chart Intelligence enabled, limit to 3 images for cost control
    logger.info("Running analysis with Chart Intelligence enabled (limit: 3 images)...")

    try:
        analysis = analyzer.analyze(
            pdf_path=pdf_path,
            source=source,
            analyze_images=True,  # ENABLE Chart Intelligence
            image_limit=3  # Cost control for testing
        )

        # Display results
        logger.info("\n" + "=" * 80)
        logger.info("RESULTS")
        logger.info("=" * 80)
        logger.info(f"Page Count: {analysis.get('page_count', 0)}")
        logger.info(f"Images Analyzed: {analysis.get('images_extracted', 0)}")
        logger.info(f"Report Type: {analysis.get('report_type', 'N/A')}")
        logger.info("")
        logger.info(f"Key Themes ({len(analysis.get('key_themes', []))}):")
        for i, theme in enumerate(analysis.get('key_themes', [])[:5], 1):
            logger.info(f"  {i}. {theme}")
        logger.info("")
        logger.info(f"Tickers Mentioned ({len(analysis.get('tickers_mentioned', []))}):")
        logger.info(f"  {analysis.get('tickers_mentioned', [])}")
        logger.info("")
        logger.info(f"Sentiment: {analysis.get('sentiment', 'N/A')}")
        logger.info(f"Conviction: {analysis.get('conviction', 0)}/10")
        logger.info(f"Time Horizon: {analysis.get('time_horizon', 'N/A')}")

        return analysis

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Test multi-source analysis."""

    logger.info("\n")
    logger.info("=" * 80)
    logger.info("MULTI-SOURCE CHART INTELLIGENCE TEST")
    logger.info("=" * 80)
    logger.info("")
    logger.info("This demonstrates Chart Intelligence analyzing:")
    logger.info("  1. 42 Macro: Large PDF with 70-80 slides (macro analysis)")
    logger.info("  2. Discord: Small PDF with 2-4 pages (options/volatility)")
    logger.info("")
    logger.info("Cost: ~$0.20 (3 images per PDF × 2 PDFs × $0.03/image)")
    logger.info("=" * 80)
    logger.info("")

    results = {}

    # Test 1: 42 Macro PDF
    macro_pdf = "downloads/42macro/20251119_154317_Around_The_Horn_-_Friday__November_7__2025.pdf"
    results["42macro"] = analyze_pdf(macro_pdf, "42macro", "TEST 1: 42 MACRO ANALYSIS")

    logger.info("\n\n")

    # Test 2: Discord PDF
    discord_pdf = "downloads/discord/20251119_142013_CRYPTO_OPTIONS_WEEKLY_18Nov25.pdf"
    results["discord"] = analyze_pdf(discord_pdf, "discord", "TEST 2: DISCORD ANALYSIS")

    # Summary
    logger.info("\n\n")
    logger.info("=" * 80)
    logger.info("MULTI-SOURCE ANALYSIS COMPLETE")
    logger.info("=" * 80)

    for source, analysis in results.items():
        if analysis:
            logger.info(f"\n{source.upper()}:")
            logger.info(f"  ✅ Success")
            logger.info(f"  - Themes: {len(analysis.get('key_themes', []))}")
            logger.info(f"  - Tickers: {len(analysis.get('tickers_mentioned', []))}")
            logger.info(f"  - Images: {analysis.get('images_extracted', 0)}")
            logger.info(f"  - Conviction: {analysis.get('conviction', 0)}/10")
        else:
            logger.info(f"\n{source.upper()}: ❌ Failed")

    logger.info("\n" + "=" * 80)
    logger.info("Chart Intelligence System operational across multiple sources!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
