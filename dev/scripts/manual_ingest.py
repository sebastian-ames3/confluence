"""
Manual Content Ingestion Script

Emergency backup when automated scrapers fail.
Simply drop a PDF into a folder and run this script to ingest it.

Usage:
    python dev/scripts/manual_ingest.py path/to/file.pdf --source 42macro
    python dev/scripts/manual_ingest.py path/to/image.png --source kt_technical
"""

import sys
import argparse
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.pdf_analyzer import PDFAnalyzerAgent
from agents.image_intelligence import ImageIntelligenceAgent
from backend.utils.db import get_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def ingest_pdf(file_path: str, source: str):
    """
    Manually ingest a PDF file.

    Args:
        file_path: Path to PDF file
        source: Source name (42macro, discord, etc.)
    """
    logger.info(f"Ingesting PDF: {file_path}")
    logger.info(f"Source: {source}")

    try:
        # Step 1: Save to raw_content table
        db = get_db()

        # Get or create source
        source_row = db.execute_query(
            "SELECT * FROM sources WHERE name = ?",
            (source,),
            fetch="one"
        )

        if not source_row:
            logger.info(f"Creating new source: {source}")
            source_id = db.insert("sources", {
                "name": source,
                "type": "manual_upload",
                "active": True
            })
        else:
            source_id = source_row["id"]

        # Insert raw content record
        raw_content_id = db.insert("raw_content", {
            "source_id": source_id,
            "content_type": "pdf",
            "file_path": str(file_path),
            "json_metadata": f'{{"manual_upload": true, "upload_time": "{datetime.now().isoformat()}"}}',
            "collected_at": datetime.now().isoformat(),
            "processed": False
        })

        logger.info(f"✓ Saved to database (raw_content id: {raw_content_id})")

        # Step 2: Analyze PDF
        logger.info("Analyzing PDF with PDFAnalyzerAgent...")
        analyzer = PDFAnalyzerAgent()

        analysis = analyzer.analyze(
            pdf_path=file_path,
            source=source,
            analyze_images=True,  # Enable chart intelligence
            image_limit=15
        )

        logger.info(f"✓ PDF analyzed successfully")
        logger.info(f"  - Key themes: {len(analysis.get('key_themes', []))}")
        logger.info(f"  - Tickers mentioned: {analysis.get('tickers_mentioned', [])}")
        logger.info(f"  - Sentiment: {analysis.get('sentiment', 'N/A')}")
        logger.info(f"  - Conviction: {analysis.get('conviction', 0)}/10")

        # Step 3: Save analysis to database
        analyzed_content_id = db.insert("analyzed_content", {
            "raw_content_id": raw_content_id,
            "agent_type": "pdf",
            "analysis_result": str(analysis),  # TODO: JSON serialize properly
            "key_themes": ", ".join(analysis.get("key_themes", [])),
            "tickers_mentioned": ", ".join(analysis.get("tickers_mentioned", [])),
            "sentiment": analysis.get("sentiment"),
            "conviction": analysis.get("conviction", 0),
            "time_horizon": analysis.get("time_horizon"),
            "analyzed_at": datetime.now().isoformat()
        })

        logger.info(f"✓ Analysis saved (analyzed_content id: {analyzed_content_id})")

        # Mark raw content as processed
        db.update("raw_content", raw_content_id, {"processed": True})

        logger.info("=" * 60)
        logger.info("SUCCESS: PDF ingested and analyzed successfully!")
        logger.info("=" * 60)

        return {
            "status": "success",
            "raw_content_id": raw_content_id,
            "analyzed_content_id": analyzed_content_id,
            "analysis": analysis
        }

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise


async def ingest_image(file_path: str, source: str):
    """
    Manually ingest an image file (chart/screenshot).

    Args:
        file_path: Path to image file
        source: Source name
    """
    logger.info(f"Ingesting image: {file_path}")
    logger.info(f"Source: {source}")

    try:
        # Step 1: Save to raw_content table
        db = get_db()

        # Get or create source
        source_row = db.execute_query(
            "SELECT * FROM sources WHERE name = ?",
            (source,),
            fetch="one"
        )

        if not source_row:
            logger.info(f"Creating new source: {source}")
            source_id = db.insert("sources", {
                "name": source,
                "type": "manual_upload",
                "active": True
            })
        else:
            source_id = source_row["id"]

        # Insert raw content record
        raw_content_id = db.insert("raw_content", {
            "source_id": source_id,
            "content_type": "image",
            "file_path": str(file_path),
            "json_metadata": f'{{"manual_upload": true, "upload_time": "{datetime.now().isoformat()}"}}',
            "collected_at": datetime.now().isoformat(),
            "processed": False
        })

        logger.info(f"✓ Saved to database (raw_content id: {raw_content_id})")

        # Step 2: Analyze image
        logger.info("Analyzing image with ImageIntelligenceAgent...")
        analyzer = ImageIntelligenceAgent()

        analysis = analyzer.analyze(
            image_path=file_path,
            source=source
        )

        logger.info(f"✓ Image analyzed successfully")
        logger.info(f"  - Tickers: {analysis.get('tickers', [])}")
        logger.info(f"  - Sentiment: {analysis.get('sentiment', 'N/A')}")
        logger.info(f"  - Main insight: {analysis.get('interpretation', {}).get('main_insight', 'N/A')}")

        # Step 3: Save analysis to database
        analyzed_content_id = db.insert("analyzed_content", {
            "raw_content_id": raw_content_id,
            "agent_type": "image",
            "analysis_result": str(analysis),
            "key_themes": ", ".join(analysis.get("key_themes", [])) if "key_themes" in analysis else "",
            "tickers_mentioned": ", ".join(analysis.get("tickers", [])) if "tickers" in analysis else "",
            "sentiment": analysis.get("sentiment"),
            "conviction": analysis.get("conviction", 0),
            "time_horizon": analysis.get("time_horizon"),
            "analyzed_at": datetime.now().isoformat()
        })

        logger.info(f"✓ Analysis saved (analyzed_content id: {analyzed_content_id})")

        # Mark raw content as processed
        db.update("raw_content", raw_content_id, {"processed": True})

        logger.info("=" * 60)
        logger.info("SUCCESS: Image ingested and analyzed successfully!")
        logger.info("=" * 60)

        return {
            "status": "success",
            "raw_content_id": raw_content_id,
            "analyzed_content_id": analyzed_content_id,
            "analysis": analysis
        }

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise


async def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Manually ingest content when scrapers fail",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dev/scripts/manual_ingest.py downloads/42macro/report.pdf --source 42macro
  python dev/scripts/manual_ingest.py downloads/kt_technical/chart.png --source kt_technical
        """
    )

    parser.add_argument("file_path", help="Path to file (PDF or image)")
    parser.add_argument("--source", required=True, help="Source name (42macro, kt_technical, discord, etc.)")

    args = parser.parse_args()

    # Validate file exists
    file_path = Path(args.file_path)
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        sys.exit(1)

    # Determine file type and route to appropriate ingestion function
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        result = await ingest_pdf(str(file_path), args.source)
    elif suffix in [".png", ".jpg", ".jpeg"]:
        result = await ingest_image(str(file_path), args.source)
    else:
        logger.error(f"Unsupported file type: {suffix}")
        logger.error("Supported types: .pdf, .png, .jpg, .jpeg")
        sys.exit(1)

    return result


if __name__ == "__main__":
    asyncio.run(main())
