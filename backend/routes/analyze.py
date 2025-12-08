"""
Content Analysis Routes

API endpoints for triggering AI analysis of raw content.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging
import json
import os

from backend.models import get_db, RawContent, AnalyzedContent
from agents.content_classifier import ContentClassifierAgent
from agents.image_intelligence import ImageIntelligenceAgent
from agents.pdf_analyzer import PDFAnalyzerAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analyze", tags=["analyze"])


# Initialize agents (singletons)
classifier_agent = None
image_agent = None
pdf_agent = None


def get_classifier():
    """Get or create classifier agent instance."""
    global classifier_agent
    if classifier_agent is None:
        classifier_agent = ContentClassifierAgent()
    return classifier_agent


def get_image_agent():
    """Get or create image intelligence agent instance."""
    global image_agent
    if image_agent is None:
        image_agent = ImageIntelligenceAgent()
    return image_agent


def get_pdf_agent():
    """Get or create PDF analyzer agent instance."""
    global pdf_agent
    if pdf_agent is None:
        pdf_agent = PDFAnalyzerAgent()
    return pdf_agent


def run_image_analysis(raw_content, metadata: Dict, db: Session) -> List[Dict]:
    """
    Run image intelligence agent on images in content.

    Args:
        raw_content: RawContent object
        metadata: Parsed metadata dict containing image_paths
        db: Database session

    Returns:
        List of image analysis results
    """
    results = []
    image_paths = metadata.get("image_paths", [])

    if not image_paths:
        logger.debug(f"No images to analyze for content {raw_content.id}")
        return results

    agent = get_image_agent()
    source_name = raw_content.source.name if raw_content.source else "unknown"

    for image_path in image_paths:
        try:
            # Check if image file exists
            if not os.path.exists(image_path):
                logger.warning(f"Image file not found: {image_path}")
                continue

            # Run image analysis
            analysis = agent.analyze(
                image_path=image_path,
                source=source_name,
                context=raw_content.content_text[:500] if raw_content.content_text else None,
                metadata=metadata
            )

            # Save analysis to database
            analyzed_content = AnalyzedContent(
                raw_content_id=raw_content.id,
                agent_type="image_intelligence",
                analysis_result=json.dumps(analysis),
                key_themes=",".join(analysis.get("key_themes", [])) if analysis.get("key_themes") else None,
                tickers_mentioned=",".join(analysis.get("tickers", [])) if analysis.get("tickers") else None,
                sentiment=analysis.get("sentiment"),
                conviction=analysis.get("conviction_score"),
                time_horizon=analysis.get("time_horizon")
            )
            db.add(analyzed_content)

            results.append({
                "image_path": image_path,
                "analysis": analysis
            })

            logger.info(f"Analyzed image {image_path} for content {raw_content.id}")

        except Exception as e:
            logger.error(f"Failed to analyze image {image_path}: {str(e)}")
            results.append({
                "image_path": image_path,
                "error": str(e)
            })

    return results


def run_text_analysis(raw_content, metadata: Dict, db: Session) -> Dict:
    """
    Analyze already-extracted text content for themes, sentiment, conviction.

    Used for 42 Macro PDFs where text is extracted locally but we still
    need to create a proper AnalyzedContent record for synthesis.

    Args:
        raw_content: RawContent object with content_text
        metadata: Parsed metadata dict
        db: Database session

    Returns:
        Analysis result
    """
    from agents.base_agent import BaseAgent

    try:
        source_name = raw_content.source.name if raw_content.source else "unknown"
        content_text = raw_content.content_text or ""
        title = metadata.get("title", "Untitled")

        # Use base agent for simple text analysis
        agent = BaseAgent()

        # Build analysis prompt
        prompt = f"""Analyze this investment research content and extract key information.

**Source**: {source_name}
**Title**: {title}

**Content**:
{content_text[:8000]}

Provide analysis as JSON:
{{
  "key_themes": ["theme1", "theme2"],
  "tickers_mentioned": ["SPY", "QQQ"],
  "market_sentiment": "bullish" | "bearish" | "neutral" | "mixed",
  "conviction_score": 1-10,
  "time_horizon": "1d" | "1w" | "1m" | "3m" | "6m+",
  "summary": "2-3 sentence summary of the key points"
}}"""

        system_prompt = """You are an investment research analyst. Extract key themes, tickers, sentiment, and conviction from the content. Be accurate and concise. Respond with JSON only."""

        analysis = agent.call_claude(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=1000,
            temperature=0.0,
            expect_json=True
        )

        # Save analysis to database
        analyzed_content = AnalyzedContent(
            raw_content_id=raw_content.id,
            agent_type="text_analyzer",
            analysis_result=json.dumps(analysis),
            key_themes=",".join(analysis.get("key_themes", [])) if analysis.get("key_themes") else None,
            tickers_mentioned=",".join(analysis.get("tickers_mentioned", [])) if analysis.get("tickers_mentioned") else None,
            sentiment=analysis.get("market_sentiment"),
            conviction=analysis.get("conviction_score"),
            time_horizon=analysis.get("time_horizon")
        )
        db.add(analyzed_content)

        logger.info(f"Analyzed text content {raw_content.id}: sentiment={analysis.get('market_sentiment')}, themes={len(analysis.get('key_themes', []))}")

        return {"analysis": analysis}

    except Exception as e:
        logger.error(f"Failed to analyze text content {raw_content.id}: {str(e)}")
        return {"error": str(e)}


def run_pdf_analysis(raw_content, metadata: Dict, db: Session) -> Dict:
    """
    Run PDF analyzer agent on PDF content.

    Args:
        raw_content: RawContent object with file_path to PDF
        metadata: Parsed metadata dict
        db: Database session

    Returns:
        PDF analysis result
    """
    file_path = raw_content.file_path

    # Check if text was already extracted locally (42 Macro case)
    # Still need to analyze the text for themes, sentiment, conviction
    if metadata.get("text_extracted") and raw_content.content_text:
        logger.info(f"PDF text already extracted locally for content {raw_content.id}, analyzing text directly")
        return run_text_analysis(raw_content, metadata, db)

    if not file_path:
        logger.warning(f"No file_path for PDF content {raw_content.id}")
        return {"error": "No file path"}

    if not os.path.exists(file_path):
        logger.warning(f"PDF file not found: {file_path}")
        return {"error": f"File not found: {file_path}"}

    try:
        agent = get_pdf_agent()
        source_name = raw_content.source.name if raw_content.source else "unknown"

        # Run PDF analysis
        analysis = agent.analyze(
            pdf_path=file_path,
            source=source_name,
            metadata=metadata,
            analyze_images=True  # Enable image extraction from PDFs
        )

        # Save analysis to database
        analyzed_content = AnalyzedContent(
            raw_content_id=raw_content.id,
            agent_type="pdf_analyzer",
            analysis_result=json.dumps(analysis),
            key_themes=",".join(analysis.get("key_themes", [])) if analysis.get("key_themes") else None,
            tickers_mentioned=",".join(analysis.get("tickers_mentioned", [])) if analysis.get("tickers_mentioned") else None,
            sentiment=analysis.get("market_sentiment"),
            conviction=analysis.get("conviction_score"),
            time_horizon=analysis.get("time_horizon")
        )
        db.add(analyzed_content)

        logger.info(f"Analyzed PDF {file_path} for content {raw_content.id}")

        return {"analysis": analysis}

    except Exception as e:
        logger.error(f"Failed to analyze PDF {file_path}: {str(e)}")
        return {"error": str(e)}


@router.post("/classify/{raw_content_id}")
async def classify_content(raw_content_id: int, db: Session = Depends(get_db)):
    """
    Classify a single piece of raw content.

    Args:
        raw_content_id: ID of raw content to classify

    Returns:
        Classification result and routing instructions
    """
    try:
        # Fetch raw content from database
        raw_content = db.query(RawContent).filter(RawContent.id == raw_content_id).first()

        if not raw_content:
            raise HTTPException(status_code=404, detail=f"Raw content {raw_content_id} not found")

        # Prepare content for classification
        content_dict = {
            "raw_content_id": raw_content.id,
            "source": raw_content.source.name if raw_content.source else "unknown",
            "content_type": raw_content.content_type,
            "content_text": raw_content.content_text,
            "file_path": raw_content.file_path,
            "url": raw_content.url,
            "metadata": json.loads(raw_content.json_metadata) if raw_content.json_metadata else {}
        }

        # Run classification
        classifier = get_classifier()
        result = classifier.classify(content_dict)

        # Save classification result to database
        analyzed_content = AnalyzedContent(
            raw_content_id=raw_content.id,
            agent_type="classifier",
            analysis_result=json.dumps(result),
            key_themes=",".join(result.get("detected_topics", [])),
            sentiment=None,  # Classifier doesn't determine sentiment
            conviction=None,  # Classifier doesn't score conviction
            time_horizon=None,
            # analyzed_at uses default from model
        )

        db.add(analyzed_content)

        # Mark raw content as processed
        raw_content.processed = True

        db.commit()
        db.refresh(analyzed_content)

        logger.info(
            f"Classified content {raw_content_id}: "
            f"{result['classification']} (priority: {result['priority']})"
        )

        return {
            "raw_content_id": raw_content_id,
            "analyzed_content_id": analyzed_content.id,
            "classification": result
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Classification failed for {raw_content_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify-batch")
async def classify_batch(
    limit: int = 10,
    only_unprocessed: bool = True,
    db: Session = Depends(get_db)
):
    """
    Classify multiple raw content items in batch.

    Args:
        limit: Maximum number of items to process
        only_unprocessed: Only process items not yet analyzed

    Returns:
        List of classification results
    """
    try:
        # Build query
        query = db.query(RawContent)

        if only_unprocessed:
            query = query.filter(RawContent.processed == False)

        # Fetch items
        items = query.limit(limit).all()

        if not items:
            return {"message": "No items to process", "count": 0}

        # Process each item
        results = []
        classifier = get_classifier()

        for raw_content in items:
            try:
                # Prepare content
                content_dict = {
                    "raw_content_id": raw_content.id,
                    "source": raw_content.source.name if raw_content.source else "unknown",
                    "content_type": raw_content.content_type,
                    "content_text": raw_content.content_text,
                    "file_path": raw_content.file_path,
                    "url": raw_content.url,
                    "metadata": json.loads(raw_content.json_metadata) if raw_content.json_metadata else {}
                }

                # Classify
                result = classifier.classify(content_dict)

                # Save classification to database
                analyzed_content = AnalyzedContent(
                    raw_content_id=raw_content.id,
                    agent_type="classifier",
                    analysis_result=json.dumps(result),
                    key_themes=",".join(result.get("detected_topics", [])),
                    sentiment=None,
                    conviction=None,
                    time_horizon=None
                )

                db.add(analyzed_content)

                # Run specialized agents based on routing
                route_to = result.get("route_to_agents", [])
                metadata = content_dict.get("metadata", {})
                image_results = []
                pdf_result = {}

                if "pdf_analyzer" in route_to:
                    pdf_result = run_pdf_analysis(raw_content, metadata, db)

                if "image_intelligence" in route_to:
                    image_results = run_image_analysis(raw_content, metadata, db)

                # Mark as processed
                raw_content.processed = True

                results.append({
                    "raw_content_id": raw_content.id,
                    "classification": result["classification"],
                    "priority": result["priority"],
                    "route_to": route_to,
                    "pdf_analyzed": "analysis" in pdf_result,
                    "images_analyzed": len([r for r in image_results if "analysis" in r])
                })

            except Exception as e:
                logger.error(f"Failed to classify content {raw_content.id}: {str(e)}")
                results.append({
                    "raw_content_id": raw_content.id,
                    "error": str(e)
                })

        # Commit all changes
        db.commit()

        logger.info(f"Batch classified {len(results)} items")

        return {
            "count": len(results),
            "results": results
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Batch classification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending")
async def get_pending_analysis(db: Session = Depends(get_db)):
    """
    Get count of content pending analysis.

    Returns:
        Count of unprocessed items by source
    """
    try:
        # Get all unprocessed items
        unprocessed = db.query(RawContent).filter(RawContent.processed == False).all()

        # Group by source
        by_source = {}
        for item in unprocessed:
            source_name = item.source.name if item.source else "unknown"
            if source_name not in by_source:
                by_source[source_name] = 0
            by_source[source_name] += 1

        return {
            "total_pending": len(unprocessed),
            "by_source": by_source
        }

    except Exception as e:
        logger.error(f"Failed to get pending analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_analysis_stats(db: Session = Depends(get_db)):
    """
    Get statistics about analyzed content.

    Returns:
        Analysis statistics
    """
    try:
        # Total raw content
        total_raw = db.query(RawContent).count()
        total_processed = db.query(RawContent).filter(RawContent.processed == True).count()

        # Total analyzed
        total_analyzed = db.query(AnalyzedContent).count()

        # Analyzed by agent type
        by_agent = {}
        agent_results = db.query(
            AnalyzedContent.agent_type,
            db.func.count(AnalyzedContent.id)
        ).group_by(AnalyzedContent.agent_type).all()

        for agent_type, count in agent_results:
            by_agent[agent_type] = count

        return {
            "total_raw_content": total_raw,
            "total_processed": total_processed,
            "total_analyzed": total_analyzed,
            "by_agent_type": by_agent,
            "processing_rate": round(total_processed / total_raw * 100, 2) if total_raw > 0 else 0
        }

    except Exception as e:
        logger.error(f"Failed to get analysis stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
