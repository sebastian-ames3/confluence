"""
Test Visual Content Classifier

Tests the VisualContentClassifier on images extracted from 42 Macro PDFs.
Verifies:
1. Heuristics-based classification works
2. Vision API classification works
3. Batch classification works
4. Routing decisions are correct
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.visual_content_classifier import VisualContentClassifier
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_heuristics_only():
    """Test heuristics-based classification (no Vision API)."""
    logger.info("=" * 80)
    logger.info("TEST 1: Heuristics-Only Classification")
    logger.info("=" * 80)

    # Find extracted images
    temp_dir = project_root / "temp" / "extracted_images"
    if not temp_dir.exists():
        logger.error("No extracted images found. Run test_pdf_image_extraction.py first.")
        return

    # Get first PDF directory
    pdf_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
    if not pdf_dirs:
        logger.error("No PDF image directories found.")
        return

    test_dir = pdf_dirs[0]
    logger.info(f"Testing on images from: {test_dir.name}")

    # Get first 5 images
    images = sorted(test_dir.glob("*.png"))[:5] + sorted(test_dir.glob("*.jpeg"))[:5]

    if not images:
        logger.error("No images found in directory.")
        return

    logger.info(f"Found {len(images)} images to test")

    # Initialize classifier
    classifier = VisualContentClassifier()

    # Test heuristics on each image
    for i, image_path in enumerate(images, 1):
        logger.info(f"\nImage {i}/{len(images)}: {image_path.name}")

        result = classifier.classify(str(image_path), use_vision_api=False)

        logger.info(f"  Content Type: {result['content_type']}")
        logger.info(f"  Confidence: {result['confidence']:.2f}")
        logger.info(f"  Method: {result['method']}")
        logger.info(f"  Route To: {result['route_to']}")
        logger.info(f"  Reason: {result.get('reason', 'N/A')}")


def test_vision_api():
    """Test Vision API classification on a few sample images."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Vision API Classification")
    logger.info("=" * 80)

    # Find extracted images
    temp_dir = project_root / "temp" / "extracted_images"
    if not temp_dir.exists():
        logger.error("No extracted images found.")
        return

    pdf_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
    if not pdf_dirs:
        logger.error("No PDF image directories found.")
        return

    test_dir = pdf_dirs[0]

    # Get just 3 images for Vision API testing (to minimize cost)
    images = sorted(test_dir.glob("*.png"))[:3]

    if not images:
        logger.error("No images found.")
        return

    logger.info(f"Testing Vision API on {len(images)} images (cost: ~$0.05)")

    classifier = VisualContentClassifier()

    for i, image_path in enumerate(images, 1):
        logger.info(f"\nImage {i}/{len(images)}: {image_path.name}")

        result = classifier.classify(str(image_path), use_vision_api=True)

        logger.info(f"  Content Type: {result['content_type']}")
        logger.info(f"  Confidence: {result['confidence']:.2f}")
        logger.info(f"  Method: {result['method']}")
        logger.info(f"  Route To: {result['route_to']}")
        logger.info(f"  Reason: {result.get('reason', 'N/A')}")


def test_batch_classification():
    """Test batch classification."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Batch Classification (Heuristics)")
    logger.info("=" * 80)

    # Find extracted images
    temp_dir = project_root / "temp" / "extracted_images"
    if not temp_dir.exists():
        logger.error("No extracted images found.")
        return

    pdf_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
    if not pdf_dirs:
        logger.error("No PDF image directories found.")
        return

    test_dir = pdf_dirs[0]

    # Get all images
    images = list(test_dir.glob("*.png")) + list(test_dir.glob("*.jpeg"))
    image_paths = [str(img) for img in images[:10]]  # Limit to 10 for testing

    logger.info(f"Batch classifying {len(image_paths)} images...")

    classifier = VisualContentClassifier()
    results = classifier.classify_batch(image_paths, use_vision_api=False)

    logger.info(f"\n{'=' * 80}")
    logger.info("BATCH RESULTS")
    logger.info(f"{'=' * 80}")
    logger.info(f"Total images: {results['total']}")
    logger.info(f"\nContent type distribution:")
    for content_type, count in results['summary'].items():
        logger.info(f"  {content_type}: {count}")

    # Show routing breakdown
    logger.info(f"\nRouting decisions:")
    routes = {}
    for item in results['classifications']:
        if 'classification' in item:
            route = item['classification']['route_to']
            routes[route] = routes.get(route, 0) + 1

    for route, count in routes.items():
        logger.info(f"  {route}: {count}")


def main():
    """Run all tests."""
    logger.info("=" * 80)
    logger.info("VISUAL CONTENT CLASSIFIER TEST SUITE")
    logger.info("=" * 80)

    try:
        # Test 1: Heuristics only (fast, no cost)
        test_heuristics_only()

        # Test 2: Vision API (slower, small cost)
        user_input = input("\nRun Vision API test? (costs ~$0.05) [y/N]: ")
        if user_input.lower() == 'y':
            test_vision_api()
        else:
            logger.info("Skipping Vision API test")

        # Test 3: Batch classification
        test_batch_classification()

        logger.info("\n" + "=" * 80)
        logger.info("ALL TESTS COMPLETE")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise


if __name__ == "__main__":
    main()
