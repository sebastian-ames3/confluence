"""
Alerting Service (PRD-045)

Monitors collection pipeline health and creates alerts when issues are detected.
This service can be called from:
- GitHub Actions scheduled jobs
- Railway cron jobs
- Manual API triggers

Alert Types:
- collection_failed: 2+ consecutive collection failures (critical)
- transcription_backlog: Pending transcriptions >24h old (high)
- source_stale: No new content in 48+ hours (medium)
- error_spike: >5 errors in 24h for a source (high)
"""

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from backend.models import (
    Alert, SourceHealth, TranscriptionStatus, RawContent, Source,
    ServiceHeartbeat, AsyncSessionLocal
)

logger = logging.getLogger(__name__)

# Configuration
MONITORED_SOURCES = {"youtube", "discord", "42macro", "substack", "kt_technical"}
VIDEO_SOURCES = {"youtube", "discord", "42macro"}

# Thresholds
CONSECUTIVE_FAILURE_THRESHOLD = 2
STALENESS_THRESHOLD_HOURS = 48
TRANSCRIPTION_BACKLOG_HOURS = 24
ERROR_SPIKE_THRESHOLD = 5

# Alert expiry (auto-dismiss after this time if not acknowledged)
ALERT_EXPIRY_HOURS = 72


async def check_and_create_alerts(db: Optional[AsyncSession] = None) -> Dict[str, Any]:
    """
    Check all sources and create alerts for detected issues.

    This is the main entry point for the alerting system.
    Can be called with an existing session or will create its own.

    Returns:
        Dict with created alerts and summary
    """
    own_session = db is None
    if own_session:
        if AsyncSessionLocal is None:
            logger.error("Async database not available")
            return {"error": "Async database not available"}
        db = AsyncSessionLocal()

    try:
        now = datetime.utcnow()
        created_alerts = []
        checked_sources = []

        for source_name in MONITORED_SOURCES:
            source_result = await _check_source(db, source_name, now)
            checked_sources.append(source_result)

            for alert_data in source_result.get("alerts", []):
                alert = await _create_alert_if_not_exists(db, **alert_data)
                if alert:
                    created_alerts.append({
                        "id": alert.id,
                        "type": alert.alert_type,
                        "source": alert.source,
                        "severity": alert.severity,
                        "message": alert.message
                    })

        # Auto-expire old alerts
        await _expire_old_alerts(db, now)

        if own_session:
            await db.commit()

        return {
            "status": "success",
            "checked_at": now.isoformat(),
            "sources_checked": len(checked_sources),
            "alerts_created": len(created_alerts),
            "new_alerts": created_alerts
        }

    except Exception as e:
        logger.error(f"Alert check failed: {e}")
        if own_session:
            await db.rollback()
        return {"error": str(e)}
    finally:
        if own_session:
            await db.close()


async def _check_source(db: AsyncSession, source_name: str, now: datetime) -> Dict[str, Any]:
    """
    Check a single source for issues and return alert data if needed.
    """
    alerts = []
    cutoff_24h = now - timedelta(hours=24)
    cutoff_staleness = now - timedelta(hours=STALENESS_THRESHOLD_HOURS)

    # Get source record
    result = await db.execute(
        select(Source).where(Source.name == source_name)
    )
    source = result.scalar_one_or_none()

    if not source:
        return {"source": source_name, "status": "not_found", "alerts": []}

    # Get or create SourceHealth record
    result = await db.execute(
        select(SourceHealth).where(SourceHealth.source_name == source_name)
    )
    health = result.scalar_one_or_none()

    if not health:
        health = SourceHealth(source_name=source_name)
        db.add(health)
        await db.flush()

    # Update health metrics
    # Count items in last 24h
    result = await db.execute(
        select(func.count(RawContent.id)).where(
            and_(
                RawContent.source_id == source.id,
                RawContent.collected_at >= cutoff_24h
            )
        )
    )
    health.items_collected_24h = result.scalar() or 0

    # Check staleness
    is_stale = (
        source.last_collected_at is None or
        source.last_collected_at < cutoff_staleness
    )
    health.is_stale = is_stale
    health.last_collection_at = source.last_collected_at
    health.updated_at = now

    # Check 1: Consecutive failures
    if health.consecutive_failures >= CONSECUTIVE_FAILURE_THRESHOLD:
        alerts.append({
            "alert_type": "collection_failed",
            "source": source_name,
            "severity": "critical",
            "message": f"{source_name} has failed {health.consecutive_failures} consecutive collections"
        })

    # Check 2: Staleness
    if is_stale and source.last_collected_at:
        hours_stale = (now - source.last_collected_at).total_seconds() / 3600
        alerts.append({
            "alert_type": "source_stale",
            "source": source_name,
            "severity": "medium",
            "message": f"No new content from {source_name} in {int(hours_stale)} hours"
        })

    # Check 3: Error spike
    if health.errors_24h > ERROR_SPIKE_THRESHOLD:
        alerts.append({
            "alert_type": "error_spike",
            "source": source_name,
            "severity": "high",
            "message": f"{source_name} has {health.errors_24h} errors in the last 24 hours"
        })

    # Check 4: Transcription backlog (for video sources)
    if source_name in VIDEO_SOURCES:
        backlog_cutoff = now - timedelta(hours=TRANSCRIPTION_BACKLOG_HOURS)

        result = await db.execute(
            select(func.count(TranscriptionStatus.id)).where(
                and_(
                    TranscriptionStatus.status == "pending",
                    TranscriptionStatus.created_at < backlog_cutoff
                )
            ).select_from(TranscriptionStatus).join(
                RawContent, TranscriptionStatus.content_id == RawContent.id
            ).where(
                RawContent.source_id == source.id
            )
        )
        backlog_count = result.scalar() or 0

        if backlog_count > 0:
            alerts.append({
                "alert_type": "transcription_backlog",
                "source": source_name,
                "severity": "high",
                "message": f"{backlog_count} {source_name} videos pending transcription for >{TRANSCRIPTION_BACKLOG_HOURS} hours"
            })

        # Update transcription metrics
        result = await db.execute(
            select(func.count(TranscriptionStatus.id)).where(
                TranscriptionStatus.status == "completed"
            ).select_from(TranscriptionStatus).join(
                RawContent, TranscriptionStatus.content_id == RawContent.id
            ).where(
                and_(
                    RawContent.source_id == source.id,
                    TranscriptionStatus.completed_at >= cutoff_24h
                )
            )
        )
        health.items_transcribed_24h = result.scalar() or 0

        # Get last transcription time
        result = await db.execute(
            select(TranscriptionStatus.completed_at).where(
                TranscriptionStatus.status == "completed"
            ).select_from(TranscriptionStatus).join(
                RawContent, TranscriptionStatus.content_id == RawContent.id
            ).where(
                RawContent.source_id == source.id
            ).order_by(TranscriptionStatus.completed_at.desc()).limit(1)
        )
        last_transcription = result.scalar_one_or_none()
        if last_transcription:
            health.last_transcription_at = last_transcription

    return {
        "source": source_name,
        "status": "checked",
        "is_stale": is_stale,
        "items_24h": health.items_collected_24h,
        "errors_24h": health.errors_24h,
        "alerts": alerts
    }


async def _create_alert_if_not_exists(
    db: AsyncSession,
    alert_type: str,
    source: str,
    severity: str,
    message: str
) -> Optional[Alert]:
    """
    Create an alert only if a similar unacknowledged alert doesn't exist.

    Prevents duplicate alerts for the same issue.
    """
    # Check for existing unacknowledged alert of same type for same source
    result = await db.execute(
        select(Alert).where(
            and_(
                Alert.alert_type == alert_type,
                Alert.source == source,
                Alert.is_acknowledged == False
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        logger.debug(f"Alert already exists: {alert_type} for {source}")
        return None

    # Create new alert
    now = datetime.utcnow()
    alert = Alert(
        alert_type=alert_type,
        source=source,
        severity=severity,
        message=message,
        created_at=now,
        expires_at=now + timedelta(hours=ALERT_EXPIRY_HOURS)
    )
    db.add(alert)
    await db.flush()

    logger.info(f"Created alert: {alert_type} ({severity}) for {source}: {message}")
    return alert


async def _expire_old_alerts(db: AsyncSession, now: datetime):
    """
    Auto-acknowledge alerts that have passed their expiry time.
    """
    result = await db.execute(
        select(Alert).where(
            and_(
                Alert.is_acknowledged == False,
                Alert.expires_at < now
            )
        )
    )
    expired = result.scalars().all()

    for alert in expired:
        alert.is_acknowledged = True
        alert.acknowledged_at = now
        alert.acknowledged_by = "system:expired"
        logger.info(f"Auto-expired alert {alert.id}: {alert.alert_type}")


async def record_collection_result(
    source_name: str,
    success: bool,
    items_collected: int = 0,
    error_message: Optional[str] = None,
    db: Optional[AsyncSession] = None
) -> Dict[str, Any]:
    """
    Record a collection result and update health metrics.

    Called by collection endpoints after each run to track
    consecutive failures and update health status.

    Args:
        source_name: Name of the source
        success: Whether collection succeeded
        items_collected: Number of items collected
        error_message: Error message if failed
        db: Optional database session

    Returns:
        Dict with updated health metrics
    """
    own_session = db is None
    if own_session:
        if AsyncSessionLocal is None:
            return {"error": "Async database not available"}
        db = AsyncSessionLocal()

    try:
        now = datetime.utcnow()

        # Get or create SourceHealth record
        result = await db.execute(
            select(SourceHealth).where(SourceHealth.source_name == source_name)
        )
        health = result.scalar_one_or_none()

        if not health:
            health = SourceHealth(source_name=source_name)
            db.add(health)

        # Update metrics
        health.last_collection_at = now
        health.updated_at = now

        if success:
            health.last_collection_status = "success"
            health.consecutive_failures = 0
        else:
            health.last_collection_status = "failed"
            health.consecutive_failures += 1
            health.errors_24h += 1

        if own_session:
            await db.commit()

        return {
            "source": source_name,
            "status": health.last_collection_status,
            "consecutive_failures": health.consecutive_failures,
            "updated_at": now.isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to record collection result: {e}")
        if own_session:
            await db.rollback()
        return {"error": str(e)}
    finally:
        if own_session:
            await db.close()


async def update_source_health_metrics(db: AsyncSession, source_name: str):
    """
    Recalculate and update all health metrics for a source.

    Called periodically or after significant events.
    """
    now = datetime.utcnow()
    cutoff_24h = now - timedelta(hours=24)

    # Get source
    result = await db.execute(
        select(Source).where(Source.name == source_name)
    )
    source = result.scalar_one_or_none()

    if not source:
        return

    # Get or create health record
    result = await db.execute(
        select(SourceHealth).where(SourceHealth.source_name == source_name)
    )
    health = result.scalar_one_or_none()

    if not health:
        health = SourceHealth(source_name=source_name)
        db.add(health)

    # Update items_collected_24h
    result = await db.execute(
        select(func.count(RawContent.id)).where(
            and_(
                RawContent.source_id == source.id,
                RawContent.collected_at >= cutoff_24h
            )
        )
    )
    health.items_collected_24h = result.scalar() or 0

    # Check staleness
    staleness_cutoff = now - timedelta(hours=STALENESS_THRESHOLD_HOURS)
    health.is_stale = (
        source.last_collected_at is None or
        source.last_collected_at < staleness_cutoff
    )

    health.last_collection_at = source.last_collected_at
    health.updated_at = now

    await db.flush()
