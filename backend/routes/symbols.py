"""
Symbol-Level Confluence Tracking API (PRD-039)

Endpoints for accessing symbol levels, state, and confluence analysis.

PRD-036: Uses verify_jwt_or_basic for JWT + Basic Auth compatibility.
PRD-048: Added staleness validation on read and concurrency lock on refresh.
"""

import logging
import asyncio
import os
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta
from pydantic import BaseModel

from backend.models import get_db, SymbolLevel, SymbolState, RawContent
from backend.utils.auth import verify_jwt_or_basic

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/symbols", tags=["symbols"])

# ============================================================================
# PRD-048: Staleness Configuration
# ============================================================================
STALENESS_THRESHOLD_HOURS = int(os.getenv("SYMBOL_STALENESS_HOURS", "48"))

# ============================================================================
# PRD-048: Concurrency Lock for Symbol Refresh
# ============================================================================
_refresh_lock = asyncio.Lock()
_refresh_in_progress = False


# ============================================================================
# Request/Response Models
# ============================================================================

class LevelUpdate(BaseModel):
    """Request model for updating a level."""
    price: Optional[float] = None
    level_type: Optional[str] = None
    direction: Optional[str] = None
    is_active: Optional[bool] = None


# ============================================================================
# PRD-048: Staleness Calculation Helper
# ============================================================================

def calculate_staleness(last_updated: Optional[datetime]) -> Dict[str, Any]:
    """
    Calculate staleness info for symbol data (PRD-048).

    Called on every read operation to provide real-time staleness status.

    Args:
        last_updated: Timestamp of last data update

    Returns:
        Dict with is_stale, hours_since_update, staleness_message
    """
    if not last_updated:
        return {
            "is_stale": True,
            "hours_since_update": None,
            "staleness_message": "Never updated"
        }

    hours_since = (datetime.utcnow() - last_updated).total_seconds() / 3600

    is_stale = hours_since > STALENESS_THRESHOLD_HOURS
    message = None

    if is_stale:
        if hours_since < 168:  # Less than a week
            message = f"Data is {round(hours_since)}h old - may be outdated"
        else:
            days = round(hours_since / 24)
            message = f"Data is {days} days old - may be outdated"

    return {
        "is_stale": is_stale,
        "hours_since_update": round(hours_since, 1),
        "staleness_message": message
    }


# ============================================================================
# Endpoints
# ============================================================================

@router.get("")
async def get_all_symbols(
    user: str = Depends(verify_jwt_or_basic),
    db: Session = Depends(get_db)
):
    """
    Get all tracked symbols with current state summary.

    Returns list of symbols with:
    - KT Technical view (wave position, bias)
    - Discord view (quadrant, IV regime)
    - Confluence score
    - Staleness warnings (PRD-048: calculated on read)
    """

    try:
        # Get all symbol states
        states = db.query(SymbolState).all()

        symbols = []
        for state in states:
            # Count active levels
            level_count = db.query(SymbolLevel).filter(
                and_(
                    SymbolLevel.symbol == state.symbol,
                    SymbolLevel.is_active == True
                )
            ).count()

            # PRD-048: Calculate staleness on read for overall symbol
            overall_staleness = calculate_staleness(state.updated_at)
            kt_staleness = calculate_staleness(state.kt_last_updated)
            discord_staleness = calculate_staleness(state.discord_last_updated)

            symbols.append({
                "symbol": state.symbol,
                "kt_view": {
                    "wave_position": state.kt_wave_position,
                    "wave_phase": state.kt_wave_phase,
                    "bias": state.kt_bias,
                    "last_updated": state.kt_last_updated.isoformat() if state.kt_last_updated else None,
                    "is_stale": kt_staleness["is_stale"],
                    "hours_since_update": kt_staleness["hours_since_update"],
                    "stale_warning": kt_staleness["staleness_message"] or state.kt_stale_warning
                },
                "discord_view": {
                    "quadrant": state.discord_quadrant,
                    "iv_regime": state.discord_iv_regime,
                    "last_updated": state.discord_last_updated.isoformat() if state.discord_last_updated else None,
                    "is_stale": discord_staleness["is_stale"],
                    "hours_since_update": discord_staleness["hours_since_update"],
                    "stale_warning": discord_staleness["staleness_message"]
                },
                "confluence": {
                    "score": state.confluence_score,
                    "aligned": state.sources_directionally_aligned
                },
                "active_levels_count": level_count,
                "updated_at": state.updated_at.isoformat() if state.updated_at else None,
                # PRD-048: Overall symbol staleness
                **overall_staleness
            })

        return {
            "symbols": symbols,
            "count": len(symbols),
            "staleness_threshold_hours": STALENESS_THRESHOLD_HOURS
        }

    except Exception as e:
        logger.error(f"Error fetching symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}")
async def get_symbol_detail(
    symbol: str,
    user: str = Depends(verify_jwt_or_basic),
    db: Session = Depends(get_db)
):
    """
    Get full detail for one symbol.

    Includes:
    - Complete state (KT + Discord)
    - All active price levels
    - Confluence analysis
    - Trade setup suggestion
    - Staleness info (PRD-048: calculated on read)
    """
    symbol = symbol.upper()

    try:
        # Get symbol state
        state = db.query(SymbolState).filter(SymbolState.symbol == symbol).first()
        if not state:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")

        # Get active levels
        levels = db.query(SymbolLevel).filter(
            and_(
                SymbolLevel.symbol == symbol,
                SymbolLevel.is_active == True
            )
        ).order_by(SymbolLevel.price.desc()).all()

        # PRD-048: Calculate staleness on read
        overall_staleness = calculate_staleness(state.updated_at)
        kt_staleness = calculate_staleness(state.kt_last_updated)
        discord_staleness = calculate_staleness(state.discord_last_updated)

        return {
            "symbol": symbol,
            # PRD-048: Overall staleness info
            **overall_staleness,
            "staleness_threshold_hours": STALENESS_THRESHOLD_HOURS,
            "kt_technical": {
                "wave_degree": state.kt_wave_degree,
                "wave_position": state.kt_wave_position,
                "wave_direction": state.kt_wave_direction,
                "wave_phase": state.kt_wave_phase,
                "bias": state.kt_bias,
                "primary_target": state.kt_primary_target,
                "primary_support": state.kt_primary_support,
                "invalidation": state.kt_invalidation,
                "notes": state.kt_notes,
                "last_updated": state.kt_last_updated.isoformat() if state.kt_last_updated else None,
                "is_stale": kt_staleness["is_stale"],
                "hours_since_update": kt_staleness["hours_since_update"],
                "stale_warning": kt_staleness["staleness_message"] or state.kt_stale_warning,
                "source_content_id": state.kt_source_content_id
            },
            "discord_options": {
                "quadrant": state.discord_quadrant,
                "iv_regime": state.discord_iv_regime,
                "strategy_rec": state.discord_strategy_rec,
                "key_strikes": state.discord_key_strikes,
                "notes": state.discord_notes,
                "last_updated": state.discord_last_updated.isoformat() if state.discord_last_updated else None,
                "is_stale": discord_staleness["is_stale"],
                "hours_since_update": discord_staleness["hours_since_update"],
                "stale_warning": discord_staleness["staleness_message"],
                "source_content_id": state.discord_source_content_id
            },
            "confluence": {
                "score": state.confluence_score,
                "aligned": state.sources_directionally_aligned,
                "summary": state.confluence_summary,
                "trade_setup": state.trade_setup_suggestion
            },
            "levels": [
                {
                    "id": level.id,
                    "type": level.level_type,
                    "price": level.price,
                    "price_upper": level.price_upper,
                    "direction": level.direction,
                    "significance": level.significance,
                    "wave_context": level.wave_context,
                    "options_context": level.options_context,
                    "fib_level": level.fib_level,
                    "context_snippet": level.context_snippet,
                    "confidence": level.confidence,
                    "source": level.source,
                    "invalidation_price": level.invalidation_price,
                    "is_stale": level.is_stale,
                    "created_at": level.created_at.isoformat() if level.created_at else None
                }
                for level in levels
            ],
            "updated_at": state.updated_at.isoformat() if state.updated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching symbol {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/levels")
async def get_symbol_levels(
    symbol: str,
    source: Optional[str] = None,
    user: str = Depends(verify_jwt_or_basic),
    db: Session = Depends(get_db)
):
    """
    Get all active price levels for a symbol.

    Args:
        symbol: Symbol ticker
        source: Optional filter by source (kt_technical or discord)
    """
    symbol = symbol.upper()

    try:
        query = db.query(SymbolLevel).filter(
            and_(
                SymbolLevel.symbol == symbol,
                SymbolLevel.is_active == True
            )
        )

        if source:
            query = query.filter(SymbolLevel.source == source)

        levels = query.order_by(SymbolLevel.price.desc()).all()

        return {
            "symbol": symbol,
            "source": source,
            "levels": [
                {
                    "id": level.id,
                    "type": level.level_type,
                    "price": level.price,
                    "price_upper": level.price_upper,
                    "direction": level.direction,
                    "context_snippet": level.context_snippet,
                    "confidence": level.confidence,
                    "source": level.source,
                    "created_at": level.created_at.isoformat() if level.created_at else None
                }
                for level in levels
            ],
            "count": len(levels)
        }

    except Exception as e:
        logger.error(f"Error fetching levels for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/confluence/opportunities")
async def get_confluence_opportunities(
    user: str = Depends(verify_jwt_or_basic),
    db: Session = Depends(get_db)
):
    """
    Get symbols where KT and Discord are directionally aligned (high confluence).

    Returns symbols with:
    - confluence_score > 0.7
    - sources_directionally_aligned = True
    - Trade setup suggestions
    - Staleness info (PRD-048)
    """

    try:
        states = db.query(SymbolState).filter(
            and_(
                SymbolState.confluence_score >= 0.7,
                SymbolState.sources_directionally_aligned == True
            )
        ).order_by(desc(SymbolState.confluence_score)).all()

        opportunities = []
        for state in states:
            # PRD-048: Calculate staleness on read
            overall_staleness = calculate_staleness(state.updated_at)
            kt_staleness = calculate_staleness(state.kt_last_updated)
            discord_staleness = calculate_staleness(state.discord_last_updated)

            opportunities.append({
                "symbol": state.symbol,
                "confluence_score": state.confluence_score,
                "kt_bias": state.kt_bias,
                "discord_quadrant": state.discord_quadrant,
                "summary": state.confluence_summary,
                "trade_setup": state.trade_setup_suggestion,
                "kt_last_updated": state.kt_last_updated.isoformat() if state.kt_last_updated else None,
                "discord_last_updated": state.discord_last_updated.isoformat() if state.discord_last_updated else None,
                # PRD-048: Staleness info
                **overall_staleness,
                "kt_is_stale": kt_staleness["is_stale"],
                "discord_is_stale": discord_staleness["is_stale"]
            })

        return {
            "opportunities": opportunities,
            "count": len(opportunities),
            "staleness_threshold_hours": STALENESS_THRESHOLD_HOURS
        }

    except Exception as e:
        logger.error(f"Error fetching confluence opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def refresh_symbol_data(
    background_tasks: BackgroundTasks,
    user: str = Depends(verify_jwt_or_basic),
    db: Session = Depends(get_db)
):
    """
    Manually trigger staleness check and recalculate confluence.

    Runs staleness check on all symbols and updates confluence scores.
    PRD-048: Added concurrency lock to prevent simultaneous refreshes.
    """
    global _refresh_in_progress

    # PRD-048: Check if refresh is already in progress
    if _refresh_lock.locked() or _refresh_in_progress:
        return {
            "status": "already_refreshing",
            "message": "Symbol refresh is already in progress. Please wait for it to complete."
        }

    async with _refresh_lock:
        _refresh_in_progress = True
        try:
            from backend.utils.staleness_manager import (
                check_and_mark_stale_data,
                update_symbol_confluence
            )

            # Run staleness check
            staleness_results = check_and_mark_stale_data(db)

            # Recalculate confluence for all symbols
            confluence_updates = []
            states = db.query(SymbolState).all()
            for state in states:
                result = update_symbol_confluence(db, state.symbol)
                if result.get("confluence", {}).get("aligned"):
                    confluence_updates.append({
                        "symbol": state.symbol,
                        "score": result["confluence"]["score"]
                    })

            logger.info(f"Manual symbol refresh completed. "
                       f"Staleness: {len(staleness_results.get('kt_stale_symbols', []))} KT, "
                       f"{len(staleness_results.get('discord_stale_symbols', []))} Discord. "
                       f"High confluence: {len(confluence_updates)} symbols")

            return {
                "message": "Symbol refresh completed",
                "status": "success",
                "staleness_check": {
                    "kt_stale_symbols": staleness_results.get("kt_stale_symbols", []),
                    "discord_stale_symbols": staleness_results.get("discord_stale_symbols", []),
                    "levels_marked_stale": staleness_results.get("stale_levels_marked", 0)
                },
                "confluence_updated": confluence_updates,
                "total_symbols_checked": len(states)
            }

        except Exception as e:
            logger.error(f"Error refreshing symbols: {e}")
            raise HTTPException(status_code=500, detail=str(e))

        finally:
            _refresh_in_progress = False


@router.post("/extract/{content_id}")
async def extract_symbols_from_content(
    content_id: int,
    force: bool = False,
    user: str = Depends(verify_jwt_or_basic),
    db: Session = Depends(get_db)
):
    """
    Manually trigger symbol extraction on specific content (PRD-039).

    Use this to re-extract symbols from existing KT Technical or Discord content.

    Args:
        content_id: ID of raw_content to process
        force: If True, re-extract even if content was already processed
    """
    from agents.symbol_level_extractor import SymbolLevelExtractor

    try:
        # Get the raw content
        raw_content = db.query(RawContent).filter(RawContent.id == content_id).first()
        if not raw_content:
            raise HTTPException(status_code=404, detail=f"Content {content_id} not found")

        # Check source eligibility
        source_name = raw_content.source.name if raw_content.source else ""
        if source_name not in ('kt_technical', 'discord'):
            raise HTTPException(
                status_code=400,
                detail=f"Source '{source_name}' not eligible for symbol extraction. Must be 'kt_technical' or 'discord'."
            )

        # Check if content has text
        content_text = raw_content.content_text
        if not content_text or len(content_text.strip()) < 100:
            raise HTTPException(
                status_code=400,
                detail="Content has insufficient text for symbol extraction (min 100 chars required)"
            )

        # Check if already has symbol extraction (unless force=True)
        if not force:
            existing_levels = db.query(SymbolLevel).filter(
                SymbolLevel.extracted_from_content_id == content_id
            ).count()
            if existing_levels > 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Content {content_id} already has {existing_levels} extracted levels. Use force=true to re-extract."
                )

        # If forcing, clear existing levels from this content
        if force:
            deleted = db.query(SymbolLevel).filter(
                SymbolLevel.extracted_from_content_id == content_id
            ).delete()
            logger.info(f"Force re-extraction: cleared {deleted} existing levels for content {content_id}")

        # Run extraction
        extractor = SymbolLevelExtractor()
        extraction_result = extractor.extract_from_transcript(
            transcript=content_text,
            source=source_name,
            content_id=content_id
        )

        # Save to database
        if extraction_result.get("symbols"):
            save_summary = extractor.save_extraction_to_db(
                db=db,
                extraction_result=extraction_result,
                source=source_name,
                content_id=content_id
            )

            logger.info(f"Manual symbol extraction for content {content_id}: "
                       f"{save_summary['symbols_processed']} symbols, "
                       f"{save_summary['levels_created']} levels")

            return {
                "message": "Symbol extraction completed",
                "content_id": content_id,
                "source": source_name,
                "symbols_extracted": save_summary["symbols_processed"],
                "levels_created": save_summary["levels_created"],
                "states_updated": save_summary["states_updated"],
                "symbols": [s.get("symbol") for s in extraction_result.get("symbols", [])],
                "extraction_confidence": extraction_result.get("extraction_confidence"),
                "errors": save_summary.get("errors", [])
            }
        else:
            return {
                "message": "No symbols found in content",
                "content_id": content_id,
                "source": source_name,
                "symbols_extracted": 0,
                "levels_created": 0
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting symbols from content {content_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-image/{content_id}")
async def extract_symbols_from_image(
    content_id: int,
    force: bool = False,
    user: str = Depends(verify_jwt_or_basic),
    db: Session = Depends(get_db)
):
    """
    Extract symbols from image content (Stock Compass or charts).

    Use this for Discord Stock Compass images or KT Technical chart images.

    Args:
        content_id: ID of raw_content with image
        force: If True, re-extract even if already processed
    """
    from agents.symbol_level_extractor import SymbolLevelExtractor
    import os
    import tempfile
    import httpx

    try:
        # Get the raw content
        raw_content = db.query(RawContent).filter(RawContent.id == content_id).first()
        if not raw_content:
            raise HTTPException(status_code=404, detail=f"Content {content_id} not found")

        # Check source eligibility
        source_name = raw_content.source.name if raw_content.source else ""
        if source_name not in ('kt_technical', 'discord'):
            raise HTTPException(
                status_code=400,
                detail=f"Source '{source_name}' not eligible. Must be 'kt_technical' or 'discord'."
            )

        # Check content type is image
        if raw_content.content_type != 'image':
            raise HTTPException(
                status_code=400,
                detail=f"Content type '{raw_content.content_type}' is not an image. Use /extract/ for text content."
            )

        # Get image file - try local first, then download from URL
        file_path = raw_content.file_path
        temp_file = None

        if file_path and os.path.exists(file_path):
            # Local file exists
            image_path = file_path
        elif raw_content.url:
            # Download from URL to temp file
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(raw_content.url, timeout=30.0)
                    response.raise_for_status()

                    # Determine extension from URL or content-type
                    ext = '.png'
                    if '.jpg' in raw_content.url or '.jpeg' in raw_content.url:
                        ext = '.jpg'
                    elif '.webp' in raw_content.url:
                        ext = '.webp'

                    # Save to temp file
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                    temp_file.write(response.content)
                    temp_file.close()
                    image_path = temp_file.name
                    logger.info(f"Downloaded image from URL to {image_path}")
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to download image from URL: {str(e)}"
                )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"No image file or URL available for content {content_id}"
            )

        try:
            # Initialize extractor
            extractor = SymbolLevelExtractor()

            # Determine extraction method based on source
            if source_name == 'discord':
                # Discord images are typically Stock Compass
                extraction_result = extractor.extract_from_compass_image(
                    image_path=image_path,
                    content_id=content_id
                )

                # Save compass data
                if extraction_result.get("compass_data"):
                    save_summary = extractor.save_compass_to_db(
                        db=db,
                        compass_result=extraction_result,
                        content_id=content_id
                    )

                    return {
                        "message": "Compass extraction completed",
                        "content_id": content_id,
                        "source": source_name,
                        "extraction_type": "compass",
                        "symbols_extracted": save_summary["symbols_processed"],
                        "states_updated": save_summary["states_updated"],
                        "symbols": [item.get("symbol") for item in extraction_result.get("compass_data", [])],
                        "extraction_confidence": extraction_result.get("extraction_confidence"),
                        "errors": save_summary.get("errors", [])
                    }
                else:
                    return {
                        "message": "No compass data found in image",
                        "content_id": content_id,
                        "source": source_name,
                        "symbols_extracted": 0
                    }
            else:
                # KT Technical images are charts
                extraction_result = extractor.extract_from_chart_image(
                    image_path=image_path,
                    content_id=content_id
                )

                # Save chart extraction (uses same method as transcript)
                if extraction_result.get("symbols"):
                    save_summary = extractor.save_extraction_to_db(
                        db=db,
                        extraction_result=extraction_result,
                        source=source_name,
                        content_id=content_id
                    )

                    return {
                        "message": "Chart extraction completed",
                        "content_id": content_id,
                        "source": source_name,
                        "extraction_type": "chart",
                        "symbols_extracted": save_summary["symbols_processed"],
                        "levels_created": save_summary["levels_created"],
                        "symbols": [s.get("symbol") for s in extraction_result.get("symbols", [])],
                        "extraction_confidence": extraction_result.get("extraction_confidence"),
                        "errors": save_summary.get("errors", [])
                    }
                else:
                    return {
                        "message": "No symbols found in chart image",
                        "content_id": content_id,
                        "source": source_name,
                        "symbols_extracted": 0
                    }
        finally:
            # Clean up temp file if created
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting from image {content_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/levels/{level_id}")
async def update_level(
    level_id: int,
    updates: LevelUpdate,
    user: str = Depends(verify_jwt_or_basic),
    db: Session = Depends(get_db)
):
    """
    User override for AI extraction errors.

    Allows editing: price, level_type, direction, is_active (dismiss).
    """

    try:
        level = db.query(SymbolLevel).filter(SymbolLevel.id == level_id).first()
        if not level:
            raise HTTPException(status_code=404, detail=f"Level {level_id} not found")

        # Apply updates
        if updates.price is not None:
            level.price = updates.price
        if updates.level_type is not None:
            level.level_type = updates.level_type
        if updates.direction is not None:
            level.direction = updates.direction
        if updates.is_active is not None:
            level.is_active = updates.is_active

        # Track edit
        level.invalidated_at = datetime.utcnow()
        level.invalidation_reason = "User edited"

        db.commit()

        logger.info(f"Level {level_id} updated by user")

        return {
            "message": "Level updated successfully",
            "level_id": level_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating level {level_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/levels/{level_id}")
async def dismiss_level(
    level_id: int,
    user: str = Depends(verify_jwt_or_basic),
    db: Session = Depends(get_db)
):
    """Mark a level as inactive (AI made an error)."""

    try:
        level = db.query(SymbolLevel).filter(SymbolLevel.id == level_id).first()
        if not level:
            raise HTTPException(status_code=404, detail=f"Level {level_id} not found")

        level.is_active = False
        level.invalidated_at = datetime.utcnow()
        level.invalidation_reason = "User dismissed"

        db.commit()

        logger.info(f"Level {level_id} dismissed by user")

        return {
            "message": "Level dismissed successfully",
            "level_id": level_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error dismissing level {level_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
