"""
Test Transcript-Chart Matcher

Tests the TranscriptChartMatcher on a 42 Macro video + PDF pair to verify:
1. Chart mentions are extracted from transcript
2. Mentions are matched to PDF images
3. Cost reduction is achieved (analyzing ~15 vs ~70 images)
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.transcript_chart_matcher import TranscriptChartMatcher
from agents.pdf_analyzer import PDFAnalyzerAgent
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_with_sample_transcript():
    """
    Test with a sample 42 Macro-style transcript.

    In production, this would use real video transcripts.
    """

    logger.info("=" * 80)
    logger.info("TRANSCRIPT-CHART MATCHER TEST")
    logger.info("=" * 80)

    # Sample transcript (simulating 42 Macro style)
    sample_transcript = """
    Good morning everyone, Darius Dale here with your macro scouting report.

    Looking at the S&P 500 chart, we can see a clear breakout above the 5800 level.
    The momentum here is strong and we're seeing follow-through.

    Moving to the dollar index, the DXY is showing some weakness which is
    supportive of risk assets. This chart shows the dollar breaking below
    key support at 103.

    Now let's talk about the VIX. Volatility has been compressed and we're
    sitting at multi-month lows around 14. This is a complacent market.

    On the inflation front, CPI data came in as expected. Looking at the
    CPI chart, we see core inflation moderating to 3.2% year-over-year.

    For bonds, the 10-year yield is holding steady at 4.2%. The TLT chart
    shows treasuries consolidating in a tight range.

    In crypto, Bitcoin continues its impressive run. The BTC chart shows
    strong momentum with price now above 95,000.

    That's it for today's macro update. We'll continue monitoring these charts.
    """

    # Find a 42 Macro PDF to test with
    pdf_path = "downloads/42macro/20251119_154317_Around_The_Horn_-_Friday__November_7__2025.pdf"

    if not os.path.exists(pdf_path):
        logger.error(f"Test PDF not found: {pdf_path}")
        logger.info("Run test_pdf_image_extraction.py first to extract images")
        return

    # Step 1: Extract images from PDF
    logger.info("\n" + "=" * 80)
    logger.info("STEP 1: Extract Images from PDF")
    logger.info("=" * 80)

    pdf_analyzer = PDFAnalyzerAgent()
    extracted_images = pdf_analyzer.extract_images(pdf_path)

    logger.info(f"Extracted {len(extracted_images)} images from PDF")

    # Step 2: Run transcript-chart matcher
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: Match Transcript to Charts")
    logger.info("=" * 80)

    matcher = TranscriptChartMatcher()
    result = matcher.prioritize_for_analysis(
        transcript=sample_transcript,
        all_images=extracted_images,
        max_analyze=15  # Analyze top 15 mentioned charts
    )

    # Display results
    logger.info("\n" + "=" * 80)
    logger.info("RESULTS")
    logger.info("=" * 80)
    logger.info(f"Status: {result['status']}")
    logger.info(f"Total images in PDF: {len(extracted_images)}")
    logger.info(f"Images to analyze: {len(result['images_to_analyze'])}")

    if result['status'] == 'success':
        logger.info(f"Chart mentions found: {len(result['chart_mentions'])}")
        logger.info(f"Matched images: {len(result['matched_images'])}")
        logger.info(f"High priority: {result['high_priority_count']}")
        logger.info(f"Medium priority: {result['medium_priority_count']}")
        logger.info(f"Cost reduction: {result['cost_reduction_pct']:.1f}%")

        logger.info("\nChart topics detected:")
        for mention in result['chart_mentions'][:5]:
            logger.info(f"  - {mention['topics'][:3]} (confidence: {mention['confidence']:.2f})")

        logger.info("\nTop matched images:")
        for match in result['matched_images'][:5]:
            img = match['image_metadata']
            logger.info(f"  - Page {img['page_number']}: score={match['match_score']:.2f}, topics={match['matched_topics']}")

    elif result['status'] == 'no_mentions':
        logger.warning(f"No chart mentions found - fallback: {result['fallback_reason']}")

    elif result['status'] == 'no_matches':
        logger.warning(f"No matches found - fallback: {result['fallback_reason']}")
        logger.info(f"Chart mentions: {len(result.get('chart_mentions', []))}")

    # Cost analysis
    logger.info("\n" + "=" * 80)
    logger.info("COST ANALYSIS")
    logger.info("=" * 80)

    without_matching = len(extracted_images) * 0.03  # $0.03 per image
    with_matching = len(result['images_to_analyze']) * 0.03
    savings = without_matching - with_matching
    savings_pct = (savings / without_matching * 100) if without_matching > 0 else 0

    logger.info(f"Without matching: ${without_matching:.2f} ({len(extracted_images)} images)")
    logger.info(f"With matching: ${with_matching:.2f} ({len(result['images_to_analyze'])} images)")
    logger.info(f"Savings: ${savings:.2f} ({savings_pct:.1f}%)")

    logger.info("\n" + "=" * 80)
    logger.info("✅ TEST COMPLETE")
    logger.info("=" * 80)

    return result


def test_extraction_only():
    """Quick test of just the mention extraction."""

    sample_text = """
    Looking at the S&P 500 chart, we see a breakout.
    The dollar chart shows weakness.
    Moving to the VIX, volatility is compressed.
    """

    matcher = TranscriptChartMatcher()
    mentions = matcher.extract_chart_mentions(sample_text)

    logger.info(f"Mentions extracted: {len(mentions)}")
    for mention in mentions:
        logger.info(f"  - {mention['topics']} (confidence: {mention['confidence']:.2f})")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        # Quick test of extraction only
        test_extraction_only()
    else:
        # Full test with PDF
        test_with_sample_transcript()
