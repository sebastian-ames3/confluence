"""
Health Monitoring Endpoints (PRD-045)

API endpoints for monitoring collection pipeline health, transcription status,
and source health. Exposes health data for dashboard and GitHub Actions.

This addresses the critical issue where collection failures went undetected
for ~1 month (YouTube transcription outage).
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import json

from backend.models import (
    get_async_db, TranscriptionStatus, SourceHealth, Alert,
    RawContent, Source, ServiceHeartbeat
)
from backend.services.alerting import check_and_create_alerts, record_collection_result

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])

# Source categories
VIDEO_SOURCES = {"youtube", "discord", "42macro"}
MONITORED_SOURCES = {"youtube", "discord", "42macro", "substack", "kt_technical"}

# Thresholds
STALENESS_THRESHOLD_HOURS = 48
TRANSCRIPTION_BACKLOG_THRESHOLD_HOURS = 24


def _calculate_overall_status(sources: Dict[str, Any]) -> str:
    """Calculate overall health status from individual source statuses."""
    statuses = [s.get("status") for s in sources.values()]

    if any(s == "critical" for s in statuses):
        return "critical"
    elif any(s == "degraded" for s in statuses):
        return "degraded"
    elif any(s == "stale" for s in statuses):
        return "degraded"
    else:
        return "healthy"


@router.get("/sources")
async def get_all_source_health(
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Get health status for all monitored sources.

    Returns per-source metrics including:
    - Collection status and timing
    - Transcription status (for video sources)
    - Error counts and staleness indicators
    - Active alerts

    Response format:
    {
        "sources": {
            "youtube": { status, last_collection, items_24h, ... },
            "discord": { ... },
            ...
        },
        "overall_status": "healthy|degraded|critical",
        "alerts": [...]
    }
    """
    try:
        now = datetime.utcnow()
        cutoff_24h = now - timedelta(hours=24)
        cutoff_staleness = now - timedelta(hours=STALENESS_THRESHOLD_HOURS)

        sources_health = {}

        for source_name in MONITORED_SOURCES:
            # Get source record
            result = await db.execute(
                select(Source).where(Source.name == source_name)
            )
            source = result.scalar_one_or_none()

            if not source:
                sources_health[source_name] = {
                    "status": "unknown",
                    "last_collection": None,
                    "items_24h": 0,
                    "errors_24h": 0,
                    "is_stale": True,
                    "message": f"Source '{source_name}' not configured"
                }
                continue

            # Count items collected in last 24h
            result = await db.execute(
                select(func.count(RawContent.id)).where(
                    and_(
                        RawContent.source_id == source.id,
                        RawContent.collected_at >= cutoff_24h
                    )
                )
            )
            items_24h = result.scalar() or 0

            # Check staleness
            is_stale = (
                source.last_collected_at is None or
                source.last_collected_at < cutoff_staleness
            )

            # Get cached health metrics if available
            result = await db.execute(
                select(SourceHealth).where(SourceHealth.source_name == source_name)
            )
            health_record = result.scalar_one_or_none()

            consecutive_failures = health_record.consecutive_failures if health_record else 0
            errors_24h = health_record.errors_24h if health_record else 0

            # Build source health info
            source_info = {
                "last_collection": source.last_collected_at.isoformat() if source.last_collected_at else None,
                "items_24h": items_24h,
                "errors_24h": errors_24h,
                "consecutive_failures": consecutive_failures,
                "is_stale": is_stale,
            }

            # Determine status
            if consecutive_failures >= 2:
                source_info["status"] = "critical"
                source_info["message"] = f"{consecutive_failures} consecutive collection failures"
            elif is_stale:
                source_info["status"] = "stale"
                source_info["message"] = f"No new content in {STALENESS_THRESHOLD_HOURS}+ hours"
            elif errors_24h > 5:
                source_info["status"] = "degraded"
                source_info["message"] = f"{errors_24h} errors in last 24 hours"
            else:
                source_info["status"] = "healthy"
                source_info["message"] = "Operating normally"

            # Add video-specific metrics
            if source_name in VIDEO_SOURCES:
                # Get transcription stats
                result = await db.execute(
                    select(
                        func.count(TranscriptionStatus.id).filter(
                            TranscriptionStatus.status == "pending"
                        ),
                        func.count(TranscriptionStatus.id).filter(
                            TranscriptionStatus.status == "completed"
                        ),
                        func.count(TranscriptionStatus.id).filter(
                            TranscriptionStatus.status == "failed"
                        ),
                    ).select_from(TranscriptionStatus).join(
                        RawContent, TranscriptionStatus.content_id == RawContent.id
                    ).where(
                        RawContent.source_id == source.id
                    )
                )
                row = result.one()
                pending, completed, failed = row

                source_info["transcription"] = {
                    "pending": pending,
                    "completed": completed,
                    "failed": failed
                }

                # Get last transcription time
                if health_record and health_record.last_transcription_at:
                    source_info["last_transcription"] = health_record.last_transcription_at.isoformat()

                # Check for transcription backlog
                result = await db.execute(
                    select(func.count(TranscriptionStatus.id)).where(
                        and_(
                            TranscriptionStatus.status == "pending",
                            TranscriptionStatus.created_at < now - timedelta(hours=TRANSCRIPTION_BACKLOG_THRESHOLD_HOURS)
                        )
                    ).select_from(TranscriptionStatus).join(
                        RawContent, TranscriptionStatus.content_id == RawContent.id
                    ).where(
                        RawContent.source_id == source.id
                    )
                )
                old_pending = result.scalar() or 0

                if old_pending > 0:
                    source_info["status"] = "degraded" if source_info["status"] == "healthy" else source_info["status"]
                    source_info["transcription"]["backlog"] = old_pending
                    source_info["message"] = f"{old_pending} transcriptions pending >24h"

            sources_health[source_name] = source_info

        # Get active alerts
        result = await db.execute(
            select(Alert).where(Alert.is_acknowledged == False).order_by(Alert.created_at.desc()).limit(10)
        )
        alerts = result.scalars().all()

        alerts_list = [
            {
                "id": alert.id,
                "type": alert.alert_type,
                "source": alert.source,
                "severity": alert.severity,
                "message": alert.message,
                "created_at": alert.created_at.isoformat()
            }
            for alert in alerts
        ]

        return {
            "sources": sources_health,
            "overall_status": _calculate_overall_status(sources_health),
            "alerts": alerts_list,
            "timestamp": now.isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get source health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources/{source_name}")
async def get_source_health_detail(
    source_name: str,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Get detailed health information for a specific source.

    Includes recent collection history, error details, and
    transcription queue status for video sources.
    """
    if source_name not in MONITORED_SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown source. Valid sources: {', '.join(MONITORED_SOURCES)}"
        )

    try:
        now = datetime.utcnow()
        cutoff_7d = now - timedelta(days=7)

        # Get source
        result = await db.execute(
            select(Source).where(Source.name == source_name)
        )
        source = result.scalar_one_or_none()

        if not source:
            raise HTTPException(
                status_code=404,
                detail=f"Source '{source_name}' not found"
            )

        # Get daily collection counts for last 7 days
        daily_counts = []
        for i in range(7):
            day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)

            result = await db.execute(
                select(func.count(RawContent.id)).where(
                    and_(
                        RawContent.source_id == source.id,
                        RawContent.collected_at >= day_start,
                        RawContent.collected_at < day_end
                    )
                )
            )
            count = result.scalar() or 0
            daily_counts.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "count": count
            })

        response = {
            "source": source_name,
            "last_collected_at": source.last_collected_at.isoformat() if source.last_collected_at else None,
            "is_active": source.active,
            "daily_collection_history": list(reversed(daily_counts)),
        }

        # Add transcription details for video sources
        if source_name in VIDEO_SOURCES:
            # Get transcription queue breakdown
            result = await db.execute(
                select(
                    TranscriptionStatus.status,
                    func.count(TranscriptionStatus.id)
                ).select_from(TranscriptionStatus).join(
                    RawContent, TranscriptionStatus.content_id == RawContent.id
                ).where(
                    RawContent.source_id == source.id
                ).group_by(TranscriptionStatus.status)
            )
            status_counts = {row[0]: row[1] for row in result.all()}

            response["transcription_status"] = {
                "pending": status_counts.get("pending", 0),
                "processing": status_counts.get("processing", 0),
                "completed": status_counts.get("completed", 0),
                "failed": status_counts.get("failed", 0),
                "skipped": status_counts.get("skipped", 0)
            }

            # Get recent failures with error messages
            result = await db.execute(
                select(TranscriptionStatus).where(
                    TranscriptionStatus.status == "failed"
                ).join(
                    RawContent, TranscriptionStatus.content_id == RawContent.id
                ).where(
                    RawContent.source_id == source.id
                ).order_by(TranscriptionStatus.updated_at.desc()).limit(5)
            )
            recent_failures = result.scalars().all()

            response["recent_failures"] = [
                {
                    "content_id": f.content_id,
                    "error": f.error_message[:200] if f.error_message else None,
                    "retry_count": f.retry_count,
                    "last_attempt": f.last_attempt_at.isoformat() if f.last_attempt_at else None
                }
                for f in recent_failures
            ]

        # Get alerts for this source
        result = await db.execute(
            select(Alert).where(
                and_(
                    Alert.source == source_name,
                    Alert.is_acknowledged == False
                )
            ).order_by(Alert.created_at.desc()).limit(5)
        )
        alerts = result.scalars().all()

        response["alerts"] = [
            {
                "id": a.id,
                "type": a.alert_type,
                "severity": a.severity,
                "message": a.message,
                "created_at": a.created_at.isoformat()
            }
            for a in alerts
        ]

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get source health detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transcription")
async def get_transcription_queue_status(
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Get transcription queue status across all sources.

    Returns counts by status and lists videos that have been
    pending for longer than the threshold.
    """
    try:
        now = datetime.utcnow()
        backlog_cutoff = now - timedelta(hours=TRANSCRIPTION_BACKLOG_THRESHOLD_HOURS)

        # Get overall status counts
        result = await db.execute(
            select(
                TranscriptionStatus.status,
                func.count(TranscriptionStatus.id)
            ).group_by(TranscriptionStatus.status)
        )
        status_counts = {row[0]: row[1] for row in result.all()}

        # Get backlog details (pending > 24h)
        # Cross-check: if the RawContent already has a transcript (content_text > 200 chars),
        # the TranscriptionStatus is stale — fix it in-place and exclude from backlog
        result = await db.execute(
            select(TranscriptionStatus, RawContent).join(
                RawContent, TranscriptionStatus.content_id == RawContent.id
            ).join(
                Source, RawContent.source_id == Source.id
            ).where(
                and_(
                    TranscriptionStatus.status == "pending",
                    TranscriptionStatus.created_at < backlog_cutoff
                )
            ).order_by(TranscriptionStatus.created_at).limit(20)
        )
        backlog_items = []
        stale_reconciled = 0
        for ts, rc in result.all():
            # Check if video is actually already transcribed (stale status record)
            content_text = rc.content_text or ""
            if len(content_text) > 200:
                # Content already has transcript — reconcile stale status
                ts.status = "completed"
                ts.completed_at = now
                stale_reconciled += 1
                continue

            metadata = json.loads(rc.json_metadata) if rc.json_metadata else {}
            backlog_items.append({
                "content_id": rc.id,
                "title": metadata.get("title", rc.url or "Unknown"),
                "url": rc.url,
                "source": rc.source.name if rc.source else "unknown",
                "pending_since": ts.created_at.isoformat(),
                "hours_pending": round((now - ts.created_at).total_seconds() / 3600, 1)
            })

        if stale_reconciled > 0:
            await db.commit()
            # Adjust pending count for reconciled records
            status_counts["pending"] = max(0, status_counts.get("pending", 0) - stale_reconciled)
            status_counts["completed"] = status_counts.get("completed", 0) + stale_reconciled
            logger.info(f"Reconciled {stale_reconciled} stale TranscriptionStatus records to completed")

        return {
            "summary": {
                "pending": status_counts.get("pending", 0),
                "processing": status_counts.get("processing", 0),
                "completed": status_counts.get("completed", 0),
                "failed": status_counts.get("failed", 0),
                "skipped": status_counts.get("skipped", 0)
            },
            "backlog": {
                "count": len(backlog_items),
                "threshold_hours": TRANSCRIPTION_BACKLOG_THRESHOLD_HOURS,
                "items": backlog_items
            },
            "timestamp": now.isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get transcription queue status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_active_alerts(
    include_acknowledged: bool = False,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Get active alerts from the alerting system.

    Args:
        include_acknowledged: If True, include acknowledged alerts
    """
    try:
        query = select(Alert).order_by(Alert.severity.desc(), Alert.created_at.desc())

        if not include_acknowledged:
            query = query.where(Alert.is_acknowledged == False)

        result = await db.execute(query.limit(50))
        alerts = result.scalars().all()

        return {
            "alerts": [
                {
                    "id": a.id,
                    "type": a.alert_type,
                    "source": a.source,
                    "severity": a.severity,
                    "message": a.message,
                    "is_acknowledged": a.is_acknowledged,
                    "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
                    "acknowledged_by": a.acknowledged_by,
                    "created_at": a.created_at.isoformat(),
                    "expires_at": a.expires_at.isoformat() if a.expires_at else None
                }
                for a in alerts
            ],
            "total": len(alerts),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    acknowledged_by: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Acknowledge an alert to dismiss it from the active list.

    Args:
        alert_id: ID of the alert to acknowledge
        acknowledged_by: Optional username/identifier
    """
    try:
        result = await db.execute(
            select(Alert).where(Alert.id == alert_id)
        )
        alert = result.scalar_one_or_none()

        if not alert:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

        if alert.is_acknowledged:
            return {
                "status": "already_acknowledged",
                "alert_id": alert_id,
                "acknowledged_at": alert.acknowledged_at.isoformat()
            }

        alert.is_acknowledged = True
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = acknowledged_by or "api"

        await db.commit()

        logger.info(f"Alert {alert_id} acknowledged by {alert.acknowledged_by}")

        return {
            "status": "success",
            "alert_id": alert_id,
            "acknowledged_at": alert.acknowledged_at.isoformat(),
            "acknowledged_by": alert.acknowledged_by
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/heartbeat/all")
async def get_all_heartbeat_status(
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Get heartbeat status for all monitored services.

    Expands on the existing /heartbeat/status endpoint to include
    all sources, not just Discord.
    """
    try:
        now = datetime.utcnow()

        # Heartbeat thresholds by service (hours)
        thresholds = {
            "discord": 13,
            "42macro": 26,
            "youtube": 26,
            "substack": 26,
            "kt_technical": 26
        }

        services_status = {}

        for service_name, threshold in thresholds.items():
            result = await db.execute(
                select(ServiceHeartbeat).where(ServiceHeartbeat.service_name == service_name)
            )
            heartbeat = result.scalar_one_or_none()

            if not heartbeat:
                services_status[service_name] = {
                    "status": "never_connected",
                    "last_heartbeat": None,
                    "hours_since_heartbeat": None,
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


@router.post("/check-alerts")
async def trigger_alert_check(
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Manually trigger alert check across all sources.

    This endpoint can be called by:
    - GitHub Actions scheduled jobs
    - Railway cron jobs
    - Manual dashboard trigger

    Returns the results of the alert check including any new alerts created.
    """
    try:
        result = await check_and_create_alerts(db)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger alert check: {e}")
        raise HTTPException(status_code=500, detail=str(e))
