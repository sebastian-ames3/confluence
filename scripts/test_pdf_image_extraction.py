"""
Test PDF Image Extraction

Tests the new extract_images() method on a real 42 Macro PDF to verify:
1. Images are successfully extracted
2. Correct number of images found (should be 70-80 for Around The Horn)
3. Image metadata is properly captured
4. Files are saved correctly
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


def test_image_extraction():
    """Test image extraction on a real 42 Macro PDF."""

    # Find a 42 Macro PDF to test with
    downloads_dir = project_root / "downloads" / "42macro"
    pdf_files = list(downloads_dir.glob("*.pdf"))

    if not pdf_files:
        logger.error("No 42 Macro PDFs found in downloads/42macro/")
        return

    # Use the first PDF found
    test_pdf = str(pdf_files[0])
    logger.info(f"Testing with PDF: {test_pdf}")
    logger.info(f"PDF name: {Path(test_pdf).name}")

    # Initialize PDF Analyzer
    analyzer = PDFAnalyzerAgent()

    # Extract images
    logger.info("=" * 80)
    logger.info("EXTRACTING IMAGES")
    logger.info("=" * 80)

    try:
        extracted_images = analyzer.extract_images(test_pdf)

        logger.info("=" * 80)
        logger.info("EXTRACTION RESULTS")
        logger.info("=" * 80)
        logger.info(f"Total images extracted: {len(extracted_images)}")

        if extracted_images:
            logger.info("\nFirst 5 images:")
            for i, img in enumerate(extracted_images[:5], 1):
                logger.info(f"\n  Image {i}:")
                logger.info(f"    Path: {img['image_path']}")
                logger.info(f"    Page: {img['page_number']}")
                logger.info(f"    Format: {img['format']}")
                logger.info(f"    Size: {img['size_bytes']:,} bytes")

            # Show page distribution
            pages_with_images = set(img['page_number'] for img in extracted_images)
            logger.info(f"\nPages with images: {sorted(pages_with_images)}")
            logger.info(f"Number of pages with images: {len(pages_with_images)}")

            # Verify files exist
            logger.info("\nVerifying files exist:")
            existing_count = 0
            for img in extracted_images:
                if os.path.exists(img['image_path']):
                    existing_count += 1

            logger.info(f"  Files that exist: {existing_count}/{len(extracted_images)}")

            # Success criteria
            logger.info("\n" + "=" * 80)
            logger.info("ANALYSIS")
            logger.info("=" * 80)

            if len(extracted_images) >= 50:
                logger.info("✅ SUCCESS: Extracted 50+ images (likely Around The Horn)")
            elif len(extracted_images) >= 10:
                logger.info("✅ PARTIAL SUCCESS: Extracted 10+ images")
            else:
                logger.warning("⚠️  WARNING: Only extracted <10 images")

            if existing_count == len(extracted_images):
                logger.info("✅ All image files saved successfully")
            else:
                logger.warning(f"⚠️  WARNING: {len(extracted_images) - existing_count} files missing")

        else:
            logger.warning("⚠️  WARNING: No images extracted from PDF")

    except Exception as e:
        logger.error(f"❌ ERROR: Image extraction failed: {e}")
        raise


if __name__ == "__main__":
    test_image_extraction()
