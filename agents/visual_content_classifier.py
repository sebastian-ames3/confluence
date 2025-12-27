"""
Visual Content Classifier

Lightweight image classification to determine content type and route to appropriate analyzer.
Classifies images as: single_chart, multi_panel, table, text_only, or unknown.

This is a fast first-pass classification before full Image Intelligence analysis.
Uses Claude Vision API with minimal tokens for classification only.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class VisualContentClassifier(BaseAgent):
    """
    Agent for classifying visual content type before full analysis.

    Uses lightweight Claude Vision API call to classify image type,
    which helps route to the appropriate specialized analyzer.
    """

    # Classification types
    CONTENT_TYPES = {
        "single_chart": "Single time-series, bar, or pie chart",
        "multi_panel": "Multiple charts in one image (dashboard)",
        "table": "Data table or grid of numbers/text",
        "text_only": "Screenshot of text, logo, or decorative image",
        "unknown": "Unable to classify"
    }

    # Routing decisions based on content type
    ROUTING_MAP = {
        "single_chart": "image_intelligence",
        "multi_panel": "image_intelligence",  # May need segmentation in future
        "table": "image_intelligence",  # Could use OCR in future
        "text_only": "skip",  # No analysis needed
        "unknown": "image_intelligence"  # Analyze anyway
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-5-20250514"
    ):
        """
        Initialize Visual Content Classifier.

        Args:
            api_key: Claude API key (defaults to env var)
            model: Claude model to use (must support vision)
        """
        super().__init__(api_key=api_key, model=model)
        logger.info(f"Initialized VisualContentClassifier")

    def classify(
        self,
        image_path: str,
        use_vision_api: bool = True
    ) -> Dict[str, Any]:
        """
        Classify image content type.

        Args:
            image_path: Path to image file
            use_vision_api: Whether to use Claude Vision API (True) or heuristics only (False)

        Returns:
            Classification result with content_type and routing decision
        """
        try:
            logger.info(f"Classifying image: {image_path}")

            # Step 1: Get basic image properties
            image_properties = self._get_image_properties(image_path)

            # Step 2: Apply heuristics for quick classification
            heuristic_result = self._apply_heuristics(image_properties)

            # Step 3: If heuristics are confident, use that; otherwise use Vision API
            if heuristic_result["confidence"] >= 0.9 or not use_vision_api:
                classification = heuristic_result
                classification["method"] = "heuristics"
            else:
                # Use Claude Vision API for classification
                vision_result = self._classify_with_vision(image_path, image_properties)
                classification = vision_result
                classification["method"] = "vision_api"

            # Add routing decision
            classification["route_to"] = self.ROUTING_MAP.get(
                classification["content_type"],
                "image_intelligence"
            )

            # Add image properties
            classification["image_properties"] = image_properties

            logger.info(
                f"Classification: {classification['content_type']} "
                f"(confidence: {classification['confidence']:.2f}, "
                f"method: {classification['method']}, "
                f"route: {classification['route_to']})"
            )

            return classification

        except Exception as e:
            logger.error(f"Classification failed: {e}")
            raise

    def _get_image_properties(self, image_path: str) -> Dict[str, Any]:
        """
        Get basic image properties for heuristic classification.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary of image properties
        """
        try:
            # Open image with PIL
            img = Image.open(image_path)

            properties = {
                "width": img.width,
                "height": img.height,
                "aspect_ratio": img.width / img.height if img.height > 0 else 0,
                "format": img.format,
                "mode": img.mode,  # RGB, RGBA, L, etc.
                "file_size_bytes": os.path.getsize(image_path)
            }

            logger.debug(
                f"Image properties: {properties['width']}x{properties['height']}, "
                f"aspect={properties['aspect_ratio']:.2f}, "
                f"format={properties['format']}"
            )

            return properties

        except Exception as e:
            logger.error(f"Failed to get image properties: {e}")
            return {
                "width": 0,
                "height": 0,
                "aspect_ratio": 0,
                "format": "unknown",
                "mode": "unknown",
                "file_size_bytes": 0
            }

    def _apply_heuristics(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply heuristic rules for quick classification.

        Args:
            properties: Image properties

        Returns:
            Classification result with confidence score
        """
        width = properties.get("width", 0)
        height = properties.get("height", 0)
        aspect_ratio = properties.get("aspect_ratio", 0)
        file_size = properties.get("file_size_bytes", 0)

        # Very small images are likely logos or icons
        if width < 200 or height < 200:
            return {
                "content_type": "text_only",
                "confidence": 0.85,
                "reason": "Very small image (likely logo/icon)"
            }

        # Very small file size relative to dimensions suggests simple graphics
        if file_size > 0 and (file_size / (width * height)) < 0.1:
            return {
                "content_type": "text_only",
                "confidence": 0.7,
                "reason": "Low file size ratio (likely simple graphic)"
            }

        # Wide aspect ratio might indicate dashboard/multi-panel
        if aspect_ratio > 2.5:
            return {
                "content_type": "multi_panel",
                "confidence": 0.6,
                "reason": "Very wide aspect ratio (possible dashboard)"
            }

        # Tall aspect ratio might indicate table
        if aspect_ratio < 0.4:
            return {
                "content_type": "table",
                "confidence": 0.6,
                "reason": "Very tall aspect ratio (possible table)"
            }

        # Default: uncertain, needs Vision API
        return {
            "content_type": "unknown",
            "confidence": 0.3,
            "reason": "Heuristics inconclusive"
        }

    def _classify_with_vision(
        self,
        image_path: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Classify image using Claude Vision API.

        This is a lightweight classification call (not full analysis).

        Args:
            image_path: Path to image
            properties: Image properties

        Returns:
            Classification result
        """
        try:
            logger.info(f"Classifying with Vision API: {image_path}")

            # Load and encode image
            import base64
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            image_base64 = base64.standard_b64encode(image_bytes).decode('utf-8')

            # Determine media type
            ext = Path(image_path).suffix.lower()
            media_type_map = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg"
            }
            media_type = media_type_map.get(ext, "image/png")

            # Build classification prompt
            prompt = """Classify this image into ONE of these categories:

1. **single_chart**: A single time-series chart, bar chart, pie chart, or line graph
2. **multi_panel**: Multiple charts/graphs in one image (dashboard, grid of charts)
3. **table**: Data table, grid of numbers, spreadsheet-style data
4. **text_only**: Screenshot of text, logo, decorative image, or non-data graphic

Return ONLY a JSON object with this format:
{
    "content_type": "single_chart|multi_panel|table|text_only",
    "confidence": 0.0-1.0,
    "reason": "brief explanation"
}

Be concise. Return ONLY the JSON, no markdown formatting."""

            # Call Claude Vision API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=256,  # Minimal tokens for classification
                temperature=0.0,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            # Parse response
            response_text = response.content[0].text
            classification = self._parse_json_response(response_text)

            # Validate
            if "content_type" not in classification:
                raise ValueError("Classification response missing content_type")

            # Ensure valid content type
            if classification["content_type"] not in self.CONTENT_TYPES:
                logger.warning(
                    f"Invalid content type: {classification['content_type']}, "
                    f"defaulting to 'unknown'"
                )
                classification["content_type"] = "unknown"

            # Ensure confidence is present
            if "confidence" not in classification:
                classification["confidence"] = 0.8  # Default high confidence from Vision API

            logger.info(
                f"Vision API classification: {classification['content_type']} "
                f"({classification['confidence']:.2f})"
            )

            return classification

        except Exception as e:
            logger.error(f"Vision API classification failed: {e}")
            # Fallback to unknown
            return {
                "content_type": "unknown",
                "confidence": 0.5,
                "reason": f"Vision API error: {str(e)}"
            }

    def classify_batch(
        self,
        image_paths: list,
        use_vision_api: bool = True
    ) -> Dict[str, Any]:
        """
        Classify multiple images.

        Args:
            image_paths: List of image file paths
            use_vision_api: Whether to use Vision API

        Returns:
            Batch classification results
        """
        logger.info(f"Classifying {len(image_paths)} images...")

        results = {
            "total": len(image_paths),
            "classifications": [],
            "summary": {}
        }

        for image_path in image_paths:
            try:
                classification = self.classify(image_path, use_vision_api)
                results["classifications"].append({
                    "image_path": image_path,
                    "classification": classification
                })
            except Exception as e:
                logger.error(f"Failed to classify {image_path}: {e}")
                results["classifications"].append({
                    "image_path": image_path,
                    "error": str(e)
                })

        # Generate summary
        content_types = [
            c["classification"]["content_type"]
            for c in results["classifications"]
            if "classification" in c
        ]

        for content_type in self.CONTENT_TYPES.keys():
            count = content_types.count(content_type)
            if count > 0:
                results["summary"][content_type] = count

        logger.info(f"Batch classification complete: {results['summary']}")

        return results
