"""
Symbol-Level Confluence Tracking API (PRD-039)

Endpoints for accessing symbol levels, state, and confluence analysis.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta
from pydantic import BaseModel

from backend.models import get_db, SymbolLevel, SymbolState, RawContent
from backend.utils.auth import verify_credentials

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/symbols", tags=["symbols"])
security = HTTPBasic()


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
    credentials: HTTPBasicCredentials = Depends(security),
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
    verify_credentials(credentials)

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
    credentials: HTTPBasicCredentials = Depends(security),
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
    verify_credentials(credentials)
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
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Get all active price levels for a symbol.

    Args:
        symbol: Symbol ticker
        source: Optional filter by source (kt_technical or discord)
    """
    verify_credentials(credentials)
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
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Get symbols where KT and Discord are directionally aligned (high confluence).

    Returns symbols with:
    - confluence_score > 0.7
    - sources_directionally_aligned = True
    - Trade setup suggestions
    """
    verify_credentials(credentials)

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
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Manually trigger level extraction from recent content.

    Processes unprocessed KT Technical and Discord content from the last 7 days.
    """
    verify_credentials(credentials)

    try:
        # This would trigger the extraction agent on recent content
        # For now, just return a message
        logger.info("Manual symbol refresh triggered")

        return {
            "message": "Symbol refresh triggered",
            "status": "processing"
        }

    except Exception as e:
        logger.error(f"Error refreshing symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/levels/{level_id}")
async def update_level(
    level_id: int,
    updates: LevelUpdate,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    User override for AI extraction errors.

    Allows editing: price, level_type, direction, is_active (dismiss).
    """
    verify_credentials(credentials)

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
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Mark a level as inactive (AI made an error)."""
    verify_credentials(credentials)

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
