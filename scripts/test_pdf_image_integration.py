"""
Test PDF + Image Integration

Tests the enhanced PDF Analyzer with image analysis enabled.
Tests on MINIMAL data first (1-2 images) to verify pipeline works.

Pipeline:
1. Extract text from PDF
2. Extract images from PDF
3. Classify images (filter text_only)
4. Analyze remaining images with Vision API
5. Combine insights
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.pdf_analyzer import PDFAnalyzerAgent
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_minimal():
    """Test with minimal images (cost control)."""

    logger.info("=" * 80)
    logger.info("MINIMAL TEST: PDF + Image Integration (1-2 images)")
    logger.info("=" * 80)

    # Use the large PDF (142 images total)
    pdf_path = 'downloads/42macro/20251119_154317_Around_The_Horn_-_Friday__November_7__2025.pdf'

    if not os.path.exists(pdf_path):
        logger.error(f"PDF not found: {pdf_path}")
        return

    logger.info(f"Testing on: {Path(pdf_path).name}")
    logger.info(f"Image limit: 2 (MINIMAL COST TEST)")
    logger.info("")

    # Initialize PDF Analyzer
    analyzer = PDFAnalyzerAgent()

    # Run analysis with image analysis ENABLED, but limit to 2 images
    logger.info("Running analysis with image_analysis=True, image_limit=2...")

    try:
        analysis = analyzer.analyze(
            pdf_path=pdf_path,
            source="42macro",
            metadata={"report_type": "ath"},
            analyze_images=True,  # ENABLE image analysis
            image_limit=2  # LIMIT to 2 images for testing
        )

        logger.info("\n" + "=" * 80)
        logger.info("RESULTS")
        logger.info("=" * 80)
        logger.info(f"PDF: {analysis.get('pdf_path', 'N/A')}")
        logger.info(f"Source: {analysis.get('source', 'N/A')}")
        logger.info(f"Report Type: {analysis.get('report_type', 'N/A')}")
        logger.info(f"Page Count: {analysis.get('page_count', 0)}")
        logger.info(f"Images Analyzed: {analysis.get('images_extracted', 0)}")
        logger.info(f"\nKey Themes: {analysis.get('key_themes', [])}")
        logger.info(f"Tickers Mentioned: {analysis.get('tickers_mentioned', [])}")
        logger.info(f"Sentiment: {analysis.get('sentiment', 'N/A')}")
        logger.info(f"Conviction: {analysis.get('conviction', 0)}/10")

        logger.info("\n" + "=" * 80)
        logger.info("✅ SUCCESS: Image integration pipeline working!")
        logger.info("=" * 80)
        logger.info(f"Cost estimate: ~$0.05-0.10 (2 images analyzed with Vision API)")

    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}")
        raise


if __name__ == "__main__":
    test_minimal()
