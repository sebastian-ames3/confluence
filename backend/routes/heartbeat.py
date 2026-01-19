"""
Heartbeat Monitoring Endpoints

Tracks when critical services (like Discord collector on laptop) last checked in.
Provides alerts when services go silent.

PRD-035: Migrated to async ORM using SQLAlchemy AsyncSession.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

from backend.models import get_async_db, ServiceHeartbeat

logger = logging.getLogger(__name__)
router = APIRouter()


# Heartbeat thresholds (hours)
DISCORD_THRESHOLD_HOURS = 13  # Discord runs daily; tighter threshold for faster failure detection


@router.post("/heartbeat/discord")
async def record_discord_heartbeat(
    db: AsyncSession = Depends(get_async_db)
):
    """
    Record a heartbeat from the Discord collector (laptop script).

    Called by collectors/discord_self.py after each successful run.

    Returns:
        Status message
    """
    try:
        now = datetime.utcnow()

        # Check if heartbeat record exists
        result = await db.execute(
            select(ServiceHeartbeat).where(ServiceHeartbeat.service_name == "discord")
        )
        heartbeat = result.scalar_one_or_none()

        if heartbeat:
            # Update existing record
            heartbeat.last_heartbeat = now
            heartbeat.heartbeat_count += 1
            heartbeat.status = "healthy"
            heartbeat.updated_at = now
            logger.info(f"Discord heartbeat updated: {heartbeat.heartbeat_count} total")
        else:
            # Create new record
            heartbeat = ServiceHeartbeat(
                service_name="discord",
                last_heartbeat=now,
                heartbeat_count=1,
                status="healthy"
            )
            db.add(heartbeat)
            logger.info("Discord heartbeat created (first run)")

        await db.commit()

        return {
            "status": "success",
            "message": "Heartbeat recorded",
            "timestamp": now.isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to record Discord heartbeat: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/heartbeat/status")
async def get_heartbeat_status(
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get current status of all monitored services.

    Returns:
        Dict with service statuses, warnings, and last heartbeat times
    """
    try:
        now = datetime.utcnow()

        # Get Discord heartbeat
        result = await db.execute(
            select(ServiceHeartbeat).where(ServiceHeartbeat.service_name == "discord")
        )
        discord_heartbeat = result.scalar_one_or_none()

        if not discord_heartbeat:
            # Never received a heartbeat
            return {
                "discord": {
                    "status": "never_connected",
                    "last_heartbeat": None,
                    "hours_since_heartbeat": None,
                    "is_stale": True,
                    "alert_level": "critical",
                    "message": "Discord collector has never connected. Laptop script may not be running."
                }
            }

        # Calculate hours since last heartbeat
        hours_since = (now - discord_heartbeat.last_heartbeat).total_seconds() / 3600
        is_stale = hours_since > DISCORD_THRESHOLD_HOURS

        status = {
            "discord": {
                "status": discord_heartbeat.status,
                "last_heartbeat": discord_heartbeat.last_heartbeat.isoformat() if discord_heartbeat.last_heartbeat else None,
                "hours_since_heartbeat": round(hours_since, 1),
                "heartbeat_count": discord_heartbeat.heartbeat_count,
                "is_stale": is_stale,
                "alert_level": "critical" if is_stale else "healthy",
                "message": _get_discord_message(hours_since, is_stale)
            }
        }

        return status

    except Exception as e:
        logger.error(f"Failed to get heartbeat status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_discord_message(hours_since: float, is_stale: bool) -> str:
    """Generate user-friendly status message."""
    if is_stale:
        return f"DISCORD DISCONNECTED - Last check-in {hours_since:.1f} hours ago. Laptop script may be down."
    elif hours_since < 2:
        return f"Healthy - Last check-in {int(hours_since * 60)} minutes ago"
    else:
        return f"Healthy - Last check-in {hours_since:.1f} hours ago"
