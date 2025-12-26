"""
Staleness Manager (PRD-039)

Manages staleness tracking for symbol levels and states.
Marks data as stale after 14 days without update.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.models import SymbolLevel, SymbolState

logger = logging.getLogger(__name__)

# Default staleness threshold
STALENESS_DAYS = 14


def check_and_mark_stale_data(db: Session) -> Dict[str, Any]:
    """
    Check all symbol levels and states for staleness.
    Mark data as stale if no update in STALENESS_DAYS.

    Args:
        db: Database session

    Returns:
        Summary of stale data found
    """
    try:
        cutoff = datetime.utcnow() - timedelta(days=STALENESS_DAYS)
        results = {
            "kt_stale_symbols": [],
            "discord_stale_symbols": [],
            "stale_levels_marked": 0
        }

        # Check KT Technical staleness per symbol
        kt_stale = db.query(SymbolState).filter(
            and_(
                SymbolState.kt_last_updated.isnot(None),
                SymbolState.kt_last_updated < cutoff,
                SymbolState.kt_is_stale == False
            )
        ).all()

        for state in kt_stale:
            state.kt_is_stale = True
            state.kt_stale_warning = f"No KT update since {state.kt_last_updated.strftime('%b %d')} - levels may be invalidated"
            results["kt_stale_symbols"].append(state.symbol)

            # Mark associated levels as stale
            levels_updated = db.query(SymbolLevel).filter(
                and_(
                    SymbolLevel.symbol == state.symbol,
                    SymbolLevel.source == 'kt_technical',
                    SymbolLevel.is_stale == False,
                    SymbolLevel.is_active == True
                )
            ).update({
                'is_stale': True,
                'stale_reason': 'No source update in 14+ days'
            })
            results["stale_levels_marked"] += levels_updated

        # Check Discord staleness per symbol
        discord_stale = db.query(SymbolState).filter(
            and_(
                SymbolState.discord_last_updated.isnot(None),
                SymbolState.discord_last_updated < cutoff,
                SymbolState.discord_is_stale == False
            )
        ).all()

        for state in discord_stale:
            state.discord_is_stale = True
            results["discord_stale_symbols"].append(state.symbol)

            # Mark associated levels as stale
            levels_updated = db.query(SymbolLevel).filter(
                and_(
                    SymbolLevel.symbol == state.symbol,
                    SymbolLevel.source == 'discord',
                    SymbolLevel.is_stale == False,
                    SymbolLevel.is_active == True
                )
            ).update({
                'is_stale': True,
                'stale_reason': 'No source update in 14+ days'
            })
            results["stale_levels_marked"] += levels_updated

        db.commit()

        if results["kt_stale_symbols"] or results["discord_stale_symbols"]:
            logger.info(f"Staleness check: KT stale={results['kt_stale_symbols']}, "
                       f"Discord stale={results['discord_stale_symbols']}, "
                       f"levels marked={results['stale_levels_marked']}")

        return results

    except Exception as e:
        logger.error(f"Staleness check failed: {e}")
        db.rollback()
        raise


def refresh_staleness_for_symbol(
    db: Session,
    symbol: str,
    source: str
) -> None:
    """
    Refresh staleness when new content arrives for a symbol.
    Resets the staleness clock for that source.

    Args:
        db: Database session
        symbol: Symbol ticker
        source: Source type ('kt_technical' or 'discord')
    """
    try:
        now = datetime.utcnow()
        state = db.query(SymbolState).filter_by(symbol=symbol).first()

        if not state:
            logger.warning(f"Symbol state not found for {symbol}")
            return

        if source == 'kt_technical':
            state.kt_last_updated = now
            state.kt_is_stale = False
            state.kt_stale_warning = None
        elif source == 'discord':
            state.discord_last_updated = now
            state.discord_is_stale = False

        state.updated_at = now

        # Refresh level confirmation dates and clear stale flag
        db.query(SymbolLevel).filter(
            and_(
                SymbolLevel.symbol == symbol,
                SymbolLevel.source == source,
                SymbolLevel.is_active == True
            )
        ).update({
            'last_confirmed_at': now,
            'is_stale': False,
            'stale_reason': None
        })

        db.commit()
        logger.info(f"Refreshed staleness for {symbol} from {source}")

    except Exception as e:
        logger.error(f"Failed to refresh staleness for {symbol}: {e}")
        db.rollback()
        raise


def calculate_confluence_score(
    kt_bias: str,
    discord_quadrant: str
) -> Dict[str, Any]:
    """
    Calculate confluence score based on directional alignment.

    Confluence requires DIRECTION alignment, not just price proximity:
    - "Support at 313" (bullish) + "Buy Call quadrant" (bullish) = HIGH confluence
    - "Support at 313" (bullish) + "Sell Call quadrant" (bearish) = CONFLICT

    Args:
        kt_bias: KT Technical bias ('bullish', 'bearish', 'neutral')
        discord_quadrant: Discord quadrant ('buy_call', 'buy_put', 'sell_call', 'sell_put', 'neutral')

    Returns:
        Confluence assessment with score and alignment status
    """
    # Map quadrants to directional bias
    quadrant_bias = {
        'buy_call': 'bullish',
        'sell_put': 'bullish',
        'buy_put': 'bearish',
        'sell_call': 'bearish',
        'neutral': 'neutral'
    }

    discord_bias = quadrant_bias.get(discord_quadrant, 'neutral')

    # Check alignment
    if not kt_bias or not discord_quadrant:
        return {
            "score": 0.0,
            "aligned": False,
            "reason": "Missing data from one or both sources"
        }

    if kt_bias == 'neutral' or discord_bias == 'neutral':
        return {
            "score": 0.5,
            "aligned": False,
            "reason": "One source is neutral"
        }

    if kt_bias == discord_bias:
        # Both aligned in same direction
        score = 0.85 if kt_bias == 'bullish' else 0.85
        return {
            "score": score,
            "aligned": True,
            "reason": f"Both sources {kt_bias} aligned"
        }
    else:
        # Conflicting signals
        return {
            "score": 0.2,
            "aligned": False,
            "reason": f"CONFLICT: KT {kt_bias} vs Discord {discord_bias}"
        }


def update_symbol_confluence(db: Session, symbol: str) -> Dict[str, Any]:
    """
    Recalculate and update confluence score for a symbol.

    Args:
        db: Database session
        symbol: Symbol ticker

    Returns:
        Updated confluence data
    """
    try:
        state = db.query(SymbolState).filter_by(symbol=symbol).first()
        if not state:
            return {"error": f"Symbol {symbol} not found"}

        # Calculate confluence
        confluence = calculate_confluence_score(
            kt_bias=state.kt_bias,
            discord_quadrant=state.discord_quadrant
        )

        # Update state
        state.confluence_score = confluence["score"]
        state.sources_directionally_aligned = confluence["aligned"]
        state.confluence_summary = confluence["reason"]
        state.updated_at = datetime.utcnow()

        # Generate trade setup if aligned
        if confluence["aligned"]:
            direction = state.kt_bias
            structure = "long" if direction == "bullish" else "short"

            # Build setup suggestion
            setup_parts = []
            if state.kt_primary_target:
                setup_parts.append(f"Target: {state.kt_primary_target}")
            if state.kt_primary_support:
                setup_parts.append(f"Support: {state.kt_primary_support}")
            if state.kt_invalidation:
                setup_parts.append(f"Stop: {state.kt_invalidation}")
            if state.discord_strategy_rec:
                setup_parts.append(f"Strategy: {state.discord_strategy_rec}")

            state.trade_setup_suggestion = f"{structure.upper()} setup. " + " | ".join(setup_parts) if setup_parts else None

        db.commit()

        return {
            "symbol": symbol,
            "confluence": confluence,
            "trade_setup": state.trade_setup_suggestion
        }

    except Exception as e:
        logger.error(f"Failed to update confluence for {symbol}: {e}")
        db.rollback()
        raise
