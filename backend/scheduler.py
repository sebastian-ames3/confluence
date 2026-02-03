"""
Scheduled Tasks

Background scheduler for automated data collection (6am, 6pm daily).
Runs: YouTube, Substack, 42 Macro, KT Technical
Excluded: Discord (runs locally)

After collection, automatically generates research synthesis.
"""

import schedule
import time
import logging
from datetime import datetime
import os
import sys
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from collectors.youtube_api import YouTubeCollector
from collectors.substack_rss import SubstackCollector
from collectors.macro42_selenium import Macro42Collector
from collectors.kt_technical import KTTechnicalCollector
from backend.utils.data_helpers import safe_get_analysis_result, safe_get_analysis_preview

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def run_collection(time_label: str):
    """
    Run all collectors (except Discord).

    Args:
        time_label: "6am" or "6pm" for logging
    """
    logger.info(f"=" * 80)
    logger.info(f"Starting {time_label} collection run")
    logger.info(f"=" * 80)

    # Initialize collectors with credentials from environment
    collectors = []

    # YouTube
    youtube_api_key = os.getenv('YOUTUBE_API_KEY')
    if youtube_api_key:
        collectors.append(("YouTube", YouTubeCollector(api_key=youtube_api_key)))
    else:
        logger.warning("[YouTube] Skipping - YOUTUBE_API_KEY not set")

    # Substack
    collectors.append(("Substack", SubstackCollector()))

    # 42 Macro (using Selenium)
    macro42_email = os.getenv('MACRO42_EMAIL')
    macro42_password = os.getenv('MACRO42_PASSWORD')
    if macro42_email and macro42_password:
        collectors.append(("42 Macro", Macro42Collector(email=macro42_email, password=macro42_password, headless=True)))
    else:
        logger.warning("[42 Macro] Skipping - MACRO42_EMAIL and MACRO42_PASSWORD not set")

    # KT Technical
    kt_email = os.getenv('KT_EMAIL')
    kt_password = os.getenv('KT_PASSWORD')
    if kt_email and kt_password:
        collectors.append(("KT Technical", KTTechnicalCollector(email=kt_email, password=kt_password)))
    else:
        logger.warning("[KT Technical] Skipping - KT_EMAIL and KT_PASSWORD not set")

    results = {
        "total": len(collectors),
        "successful": 0,
        "failed": 0,
        "errors": []
    }

    for name, collector in collectors:
        try:
            logger.info(f"[{name}] Starting collection...")

            # Run full collection process (collect + save to database)
            result = await collector.run()

            # Log results
            if result["status"] == "success":
                logger.info(
                    f"[{name}] Collection complete - "
                    f"{result['saved']}/{result['collected']} items saved to database"
                )
                results["successful"] += 1
            else:
                raise Exception(result.get("error", "Unknown error"))

        except Exception as e:
            logger.error(f"[{name}] Collection failed: {e}")
            results["failed"] += 1
            results["errors"].append({"collector": name, "error": str(e)})

    # Summary
    logger.info(f"=" * 80)
    logger.info(f"{time_label} collection complete")
    logger.info(f"Successful: {results['successful']}/{results['total']}")
    logger.info(f"Failed: {results['failed']}/{results['total']}")
    if results["errors"]:
        logger.error(f"Errors encountered:")
        for error in results["errors"]:
            logger.error(f"  - {error['collector']}: {error['error']}")
    logger.info(f"=" * 80)

    # Record collection run in database
    await record_collection_run(time_label, results)

    # Generate synthesis after successful collection
    if results["successful"] > 0:
        await generate_post_collection_synthesis()

    return results


async def record_collection_run(time_label: str, results: dict):
    """Record collection run in database for status tracking."""
    try:
        from backend.models import SessionLocal, CollectionRun

        db = SessionLocal()
        try:
            run = CollectionRun(
                run_type=f"scheduled_{time_label}" if time_label in ["6am", "6pm"] else time_label,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                source_results=json.dumps({}),  # Could add per-source details here
                total_items_collected=0,  # Could track from collector results
                successful_sources=results.get("successful", 0),
                failed_sources=results.get("failed", 0),
                errors=json.dumps(results.get("errors", [])),
                status="completed" if results.get("failed", 0) == 0 else "completed"
            )
            db.add(run)
            db.commit()
            logger.info(f"Collection run recorded in database (ID: {run.id})")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to record collection run: {e}")


async def generate_post_collection_synthesis():
    """Generate research synthesis after collection completes."""
    logger.info("=" * 80)
    logger.info("Starting post-collection synthesis generation...")
    logger.info("=" * 80)

    try:
        from backend.models import (
            SessionLocal, AnalyzedContent, RawContent, Source, Synthesis,
            SymbolState, SynthesisQualityScore
        )
        from agents.synthesis_agent import SynthesisAgent
        from agents.synthesis_evaluator import SynthesisEvaluatorAgent
        from agents.theme_extractor import extract_and_track_themes
        from backend.utils.data_helpers import safe_get_analysis_result, safe_get_analysis_preview
        from datetime import timedelta

        db = SessionLocal()
        try:
            # Get content from last 24 hours
            cutoff = datetime.utcnow() - timedelta(hours=24)

            # Query analyzed content with source info
            results = db.query(AnalyzedContent, RawContent, Source).join(
                RawContent, AnalyzedContent.raw_content_id == RawContent.id
            ).join(
                Source, RawContent.source_id == Source.id
            ).filter(
                AnalyzedContent.analyzed_at >= cutoff
            ).all()

            if not results:
                logger.info("No analyzed content in last 24h - skipping synthesis")
                return

            # Build content items for synthesis
            content_items = []
            for analyzed, raw, source in results:
                analysis_data = safe_get_analysis_result(analyzed)

                try:
                    metadata = json.loads(raw.json_metadata) if raw.json_metadata else {}
                except json.JSONDecodeError:
                    metadata = {}

                content_items.append({
                    "id": raw.id,
                    "source": source.name,
                    "type": raw.content_type,
                    "title": metadata.get("title", f"{source.name} content"),
                    "timestamp": raw.collected_at.isoformat() if raw.collected_at else None,
                    "summary": analysis_data.get("summary", safe_get_analysis_preview(analyzed, 500)),
                    "themes": analyzed.key_themes.split(",") if analyzed.key_themes else [],
                    "tickers": analyzed.tickers_mentioned.split(",") if analyzed.tickers_mentioned else [],
                    "sentiment": analyzed.sentiment,
                    "conviction": analyzed.conviction,
                    "content_text": raw.content_text[:50000] if raw.content_text else "",
                    "key_quotes": analysis_data.get("key_quotes", []),
                })

            logger.info(f"Generating synthesis from {len(content_items)} content items...")

            # Get older content for re-review recommendations
            older_cutoff = datetime.utcnow() - timedelta(days=30)
            older_results = db.query(AnalyzedContent, RawContent, Source).join(
                RawContent, AnalyzedContent.raw_content_id == RawContent.id
            ).join(
                Source, RawContent.source_id == Source.id
            ).filter(
                AnalyzedContent.analyzed_at >= older_cutoff,
                AnalyzedContent.analyzed_at < cutoff
            ).all()

            older_content = []
            for analyzed, raw, source in older_results:
                analysis_data = safe_get_analysis_result(analyzed)
                try:
                    metadata = json.loads(raw.json_metadata) if raw.json_metadata else {}
                except json.JSONDecodeError:
                    metadata = {}
                older_content.append({
                    "id": raw.id,
                    "source": source.name,
                    "type": raw.content_type,
                    "title": metadata.get("title", f"{source.name} content"),
                    "timestamp": raw.collected_at.isoformat() if raw.collected_at else None,
                    "summary": analysis_data.get("summary", safe_get_analysis_preview(analyzed, 500)),
                    "themes": analyzed.key_themes.split(",") if analyzed.key_themes else [],
                    "tickers": analyzed.tickers_mentioned.split(",") if analyzed.tickers_mentioned else [],
                    "sentiment": analyzed.sentiment,
                    "conviction": analyzed.conviction,
                    "content_text": raw.content_text[:50000] if raw.content_text else "",
                    "key_quotes": analysis_data.get("key_quotes", []),
                })

            # Get KT symbol data
            kt_symbol_data = []
            try:
                symbols = db.query(SymbolState).filter(
                    SymbolState.kt_wave_count.isnot(None)
                ).all()
                kt_symbol_data = [
                    {
                        "symbol": s.symbol,
                        "wave_count": s.kt_wave_count,
                        "bias": s.kt_bias,
                        "updated_at": s.kt_updated_at.isoformat() if s.kt_updated_at else None
                    }
                    for s in symbols
                ]
            except Exception as e:
                logger.warning(f"Failed to get KT symbol data: {e}")

            # Generate synthesis
            agent = SynthesisAgent()
            result = agent.analyze(
                content_items=content_items,
                older_content=older_content,
                time_window="24h",
                kt_symbol_data=kt_symbol_data
            )

            # Extract summary for flat columns
            exec_summary = result.get("executive_summary", {})
            synthesis_text = ""
            market_regime_str = "unclear"
            if isinstance(exec_summary, dict):
                synthesis_text = exec_summary.get("synthesis_narrative", exec_summary.get("narrative", ""))
                market_regime_str = exec_summary.get("overall_tone", "unclear")

            # Save to database
            synthesis = Synthesis(
                schema_version="5.0",
                synthesis=synthesis_text,
                key_themes=json.dumps([t.get("theme", "") for t in result.get("confluence_zones", [])]),
                high_conviction_ideas=json.dumps(result.get("attention_priorities", [])),
                contradictions=json.dumps(result.get("conflict_watch", [])),
                market_regime=market_regime_str,
                catalysts=json.dumps(result.get("catalyst_calendar", [])),
                synthesis_json=json.dumps(result),
                time_window="24h",
                content_count=len(content_items),
                sources_included=json.dumps(result.get("sources_included", [])),
                generated_at=datetime.utcnow()
            )
            db.add(synthesis)
            db.commit()

            logger.info(f"Synthesis generated and saved (ID: {synthesis.id})")

            # Run quality evaluation
            if os.getenv("ENABLE_QUALITY_EVALUATION", "true").lower() == "true":
                try:
                    evaluator = SynthesisEvaluatorAgent()
                    quality_result = evaluator.evaluate(
                        synthesis_output=result,
                        original_content=content_items
                    )
                    quality_score = SynthesisQualityScore(
                        synthesis_id=synthesis.id,
                        quality_score=quality_result["quality_score"],
                        grade=quality_result["grade"],
                        confluence_detection=quality_result["confluence_detection"],
                        evidence_preservation=quality_result["evidence_preservation"],
                        source_attribution=quality_result["source_attribution"],
                        youtube_channel_granularity=quality_result["youtube_channel_granularity"],
                        nuance_retention=quality_result["nuance_retention"],
                        actionability=quality_result["actionability"],
                        theme_continuity=quality_result["theme_continuity"],
                        flags=json.dumps(quality_result.get("flags", [])),
                        prompt_suggestions=json.dumps(quality_result.get("prompt_suggestions", []))
                    )
                    db.add(quality_score)
                    db.commit()
                    logger.info(f"Quality: {quality_result['grade']} ({quality_result['quality_score']}/100)")
                except Exception as qe:
                    logger.warning(f"Quality evaluation failed (non-fatal): {qe}")

            # Extract and track themes
            try:
                extract_and_track_themes(result, db)
            except Exception as te:
                logger.warning(f"Theme extraction failed (non-fatal): {te}")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Synthesis generation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())


def collect_6am():
    """Morning collection routine - all collectors."""
    asyncio.run(run_collection("6am"))


def collect_6pm():
    """Evening collection routine - all collectors."""
    asyncio.run(run_collection("6pm"))


def run_manual_collection():
    """Manually trigger collection (for testing or on-demand)."""
    logger.info("Running manual collection...")
    return asyncio.run(run_collection("manual"))


def run_scheduler():
    """Main scheduler loop."""
    logger.info("=" * 80)
    logger.info("Macro Confluence Hub - Scheduler Started")
    logger.info("=" * 80)
    logger.info("Scheduled collections:")
    logger.info("  - 6:00 AM daily (YouTube, Substack, 42 Macro, KT Technical)")
    logger.info("  - 6:00 PM daily (YouTube, Substack, 42 Macro, KT Technical)")
    logger.info("")
    logger.info("Excluded collectors:")
    logger.info("  - Discord: Runs locally on Sebastian's laptop")
    logger.info("=" * 80)

    # Schedule daily tasks
    schedule.every().day.at("06:00").do(collect_6am)
    schedule.every().day.at("18:00").do(collect_6pm)

    # Main loop
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            time.sleep(60)  # Wait before retrying


if __name__ == "__main__":
    # Check if running as manual trigger
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        run_manual_collection()
    else:
        run_scheduler()
