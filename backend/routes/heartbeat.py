"""
Heartbeat Monitoring Endpoints

Tracks when critical services (like Discord collector on laptop) last checked in.
Provides alerts when services go silent.

PRD-035: Migrated to async ORM using SQLAlchemy AsyncSession.
PRD-045: Expanded to support heartbeats from all sources.
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


# PRD-045: Heartbeat thresholds (hours) for all sources
HEARTBEAT_THRESHOLDS = {
    "discord": 13,      # Discord runs daily; tighter threshold for faster failure detection
    "42macro": 26,      # Runs every 12h, generous buffer
    "youtube": 26,      # Runs every 12h
    "substack": 26,     # Runs every 12h
    "kt_technical": 26  # Runs every 12h
}

# Legacy constant for backwards compatibility
DISCORD_THRESHOLD_HOURS = HEARTBEAT_THRESHOLDS["discord"]


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


# PRD-045: Generic heartbeat endpoint for any source
@router.post("/heartbeat/{service_name}")
async def record_service_heartbeat(
    service_name: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Record a heartbeat from any service.

    PRD-045: Generic endpoint supporting all monitored sources.

    Args:
        service_name: Name of the service (discord, 42macro, youtube, substack, kt_technical)

    Returns:
        Status message
    """
    # Validate service name
    valid_services = set(HEARTBEAT_THRESHOLDS.keys())
    if service_name not in valid_services:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid service. Valid services: {', '.join(valid_services)}"
        )

    try:
        now = datetime.utcnow()

        # Check if heartbeat record exists
        result = await db.execute(
            select(ServiceHeartbeat).where(ServiceHeartbeat.service_name == service_name)
        )
        heartbeat = result.scalar_one_or_none()

        if heartbeat:
            # Update existing record
            heartbeat.last_heartbeat = now
            heartbeat.heartbeat_count += 1
            heartbeat.status = "healthy"
            heartbeat.updated_at = now
            logger.info(f"{service_name} heartbeat updated: {heartbeat.heartbeat_count} total")
        else:
            # Create new record
            heartbeat = ServiceHeartbeat(
                service_name=service_name,
                last_heartbeat=now,
                heartbeat_count=1,
                status="healthy"
            )
            db.add(heartbeat)
            logger.info(f"{service_name} heartbeat created (first run)")

        await db.commit()

        return {
            "status": "success",
            "message": f"Heartbeat recorded for {service_name}",
            "service": service_name,
            "heartbeat_count": heartbeat.heartbeat_count,
            "timestamp": now.isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to record {service_name} heartbeat: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/heartbeat/all")
async def get_all_heartbeat_status(
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get heartbeat status for all monitored services.

    PRD-045: New endpoint to get status for all sources at once.

    Returns:
        Dict with status for each service
    """
    try:
        now = datetime.utcnow()
        services_status = {}

        for service_name, threshold in HEARTBEAT_THRESHOLDS.items():
            result = await db.execute(
                select(ServiceHeartbeat).where(ServiceHeartbeat.service_name == service_name)
            )
            heartbeat = result.scalar_one_or_none()

            if not heartbeat:
                services_status[service_name] = {
                    "status": "never_connected",
                    "last_heartbeat": None,
                    "hours_since_heartbeat": None,
                    "heartbeat_count": 0,
                    "is_overdue": True,
                    "threshold_hours": threshold,
                    "message": f"{service_name} has never sent a heartbeat"
                }
            else:
                hours_since = (now - heartbeat.last_heartbeat).total_seconds() / 3600
                is_overdue = hours_since > threshold

                services_status[service_name] = {
                    "status": "overdue" if is_overdue else "healthy",
                    "last_heartbeat": heartbeat.last_heartbeat.isoformat(),
                    "hours_since_heartbeat": round(hours_since, 1),
                    "heartbeat_count": heartbeat.heartbeat_count,
                    "is_overdue": is_overdue,
                    "threshold_hours": threshold,
                    "message": f"Last heartbeat {hours_since:.1f}h ago" + (" (OVERDUE)" if is_overdue else "")
                }

        # Determine overall status
        statuses = [s["status"] for s in services_status.values()]
        if any(s == "never_connected" for s in statuses):
            overall = "critical"
        elif any(s == "overdue" for s in statuses):
            overall = "degraded"
        else:
            overall = "healthy"

        return {
            "services": services_status,
            "overall_status": overall,
            "timestamp": now.isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get heartbeat status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
