"""
Heartbeat Monitoring Endpoints

Tracks when critical services (like Discord collector on laptop) last checked in.
Provides alerts when services go silent.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

from backend.utils.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


# Heartbeat thresholds (hours)
DISCORD_THRESHOLD_HOURS = 25  # Discord should run daily, allow some buffer


@router.post("/heartbeat/discord")
async def record_discord_heartbeat():
    """
    Record a heartbeat from the Discord collector (laptop script).

    Called by collectors/discord_self.py after each successful run.

    Returns:
        Status message
    """
    try:
        db = get_db()

        # Check if heartbeat record exists
        row = db.execute_query(
            "SELECT * FROM service_heartbeats WHERE service_name = ?",
            ("discord",),
            fetch="one"
        )

        now = datetime.now().isoformat()

        if row:
            # Update existing record
            db.update("service_heartbeats", row["id"], {
                "last_heartbeat": now,
                "heartbeat_count": row["heartbeat_count"] + 1,
                "status": "healthy"
            })
            logger.info(f"Discord heartbeat updated: {row['heartbeat_count'] + 1} total")
        else:
            # Create new record
            db.insert("service_heartbeats", {
                "service_name": "discord",
                "last_heartbeat": now,
                "heartbeat_count": 1,
                "status": "healthy"
            })
            logger.info("Discord heartbeat created (first run)")

        return {
            "status": "success",
            "message": "Heartbeat recorded",
            "timestamp": now
        }

    except Exception as e:
        logger.error(f"Failed to record Discord heartbeat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/heartbeat/status")
async def get_heartbeat_status():
    """
    Get current status of all monitored services.

    Returns:
        Dict with service statuses, warnings, and last heartbeat times
    """
    try:
        db = get_db()

        # Ensure table exists
        _ensure_heartbeat_table(db)

        # Get Discord heartbeat
        discord_row = db.execute_query(
            "SELECT * FROM service_heartbeats WHERE service_name = ?",
            ("discord",),
            fetch="one"
        )

        now = datetime.now()

        if not discord_row:
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

        # Parse last heartbeat time
        last_heartbeat = datetime.fromisoformat(discord_row["last_heartbeat"])
        hours_since = (now - last_heartbeat).total_seconds() / 3600

        is_stale = hours_since > DISCORD_THRESHOLD_HOURS

        status = {
            "discord": {
                "status": discord_row["status"],
                "last_heartbeat": discord_row["last_heartbeat"],
                "hours_since_heartbeat": round(hours_since, 1),
                "heartbeat_count": discord_row["heartbeat_count"],
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
        return f"⚠️ DISCORD DISCONNECTED - Last check-in {hours_since:.1f} hours ago. Laptop script may be down."
    elif hours_since < 2:
        return f"✓ Healthy - Last check-in {int(hours_since * 60)} minutes ago"
    else:
        return f"✓ Healthy - Last check-in {hours_since:.1f} hours ago"


def _ensure_heartbeat_table(db):
    """Create heartbeat table if it doesn't exist."""
    try:
        db.execute_query(
            "SELECT COUNT(*) FROM service_heartbeats LIMIT 1",
            fetch="one"
        )
    except Exception:
        # Table doesn't exist, create it
        logger.info("Creating service_heartbeats table...")
        with db.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS service_heartbeats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT NOT NULL UNIQUE,
                    last_heartbeat TIMESTAMP NOT NULL,
                    heartbeat_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'healthy',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_service_heartbeats_name
                ON service_heartbeats(service_name)
            """)
        logger.info("service_heartbeats table created successfully")
