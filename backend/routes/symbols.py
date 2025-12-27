"""
Symbol-Level Confluence Tracking API (PRD-039)

Endpoints for accessing symbol levels, state, and confluence analysis.

PRD-036: Uses verify_jwt_or_basic for JWT + Basic Auth compatibility.
"""

import logging
from typing import Optional, List
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
# Request/Response Models
# ============================================================================

class LevelUpdate(BaseModel):
    """Request model for updating a level."""
    price: Optional[float] = None
    level_type: Optional[str] = None
    direction: Optional[str] = None
    is_active: Optional[bool] = None


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
    - Staleness warnings
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

            symbols.append({
                "symbol": state.symbol,
                "kt_view": {
                    "wave_position": state.kt_wave_position,
                    "wave_phase": state.kt_wave_phase,
                    "bias": state.kt_bias,
                    "last_updated": state.kt_last_updated.isoformat() if state.kt_last_updated else None,
                    "is_stale": state.kt_is_stale,
                    "stale_warning": state.kt_stale_warning
                },
                "discord_view": {
                    "quadrant": state.discord_quadrant,
                    "iv_regime": state.discord_iv_regime,
                    "last_updated": state.discord_last_updated.isoformat() if state.discord_last_updated else None,
                    "is_stale": state.discord_is_stale
                },
                "confluence": {
                    "score": state.confluence_score,
                    "aligned": state.sources_directionally_aligned
                },
                "active_levels_count": level_count,
                "updated_at": state.updated_at.isoformat() if state.updated_at else None
            })

        return {
            "symbols": symbols,
            "count": len(symbols)
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

        return {
            "symbol": symbol,
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
                "is_stale": state.kt_is_stale,
                "stale_warning": state.kt_stale_warning,
                "source_content_id": state.kt_source_content_id
            },
            "discord_options": {
                "quadrant": state.discord_quadrant,
                "iv_regime": state.discord_iv_regime,
                "strategy_rec": state.discord_strategy_rec,
                "key_strikes": state.discord_key_strikes,
                "notes": state.discord_notes,
                "last_updated": state.discord_last_updated.isoformat() if state.discord_last_updated else None,
                "is_stale": state.discord_is_stale,
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
            opportunities.append({
                "symbol": state.symbol,
                "confluence_score": state.confluence_score,
                "kt_bias": state.kt_bias,
                "discord_quadrant": state.discord_quadrant,
                "summary": state.confluence_summary,
                "trade_setup": state.trade_setup_suggestion,
                "kt_last_updated": state.kt_last_updated.isoformat() if state.kt_last_updated else None,
                "discord_last_updated": state.discord_last_updated.isoformat() if state.discord_last_updated else None
            })

        return {
            "opportunities": opportunities,
            "count": len(opportunities)
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
    """

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
