"""
WebSocket Route for Real-Time Dashboard Updates

Provides real-time push notifications for:
- New content collected
- Analysis completed
- Confluence scores updated
- Theme changes
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept and track new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove disconnected WebSocket."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.

    Messages sent to clients:
    - {"type": "new_analysis", "data": {...}}
    - {"type": "collection_complete", "data": {...}}
    - {"type": "confluence_update", "data": {...}}
    - {"type": "theme_update", "data": {...}}
    """
    await manager.connect(websocket)

    try:
        while True:
            # Keep connection alive by receiving messages
            # Clients can send heartbeat pings
            data = await websocket.receive_text()

            # Echo back for heartbeat
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def broadcast_new_analysis(analysis_data: dict):
    """
    Broadcast when new content is analyzed.

    Args:
        analysis_data: Analysis result dictionary
    """
    message = {
        "type": "new_analysis",
        "timestamp": analysis_data.get("analyzed_at"),
        "data": {
            "source": analysis_data.get("source"),
            "content_type": analysis_data.get("content_type"),
            "key_themes": analysis_data.get("key_themes", []),
            "sentiment": analysis_data.get("sentiment"),
            "conviction": analysis_data.get("conviction")
        }
    }
    await manager.broadcast(message)


async def broadcast_collection_complete(collection_data: dict):
    """
    Broadcast when data collection completes.

    Args:
        collection_data: Collection result dictionary
    """
    message = {
        "type": "collection_complete",
        "timestamp": collection_data.get("completed_at"),
        "data": {
            "source": collection_data.get("source"),
            "items_collected": collection_data.get("count", 0),
            "status": collection_data.get("status")
        }
    }
    await manager.broadcast(message)


async def broadcast_confluence_update(confluence_data: dict):
    """
    Broadcast when confluence scores are updated.

    Args:
        confluence_data: Confluence score dictionary
    """
    message = {
        "type": "confluence_update",
        "timestamp": confluence_data.get("scored_at"),
        "data": {
            "total_score": confluence_data.get("total_score"),
            "core_score": confluence_data.get("core_score"),
            "meets_threshold": confluence_data.get("meets_threshold"),
            "themes": confluence_data.get("key_themes", [])
        }
    }
    await manager.broadcast(message)


async def broadcast_theme_update(theme_data: dict):
    """
    Broadcast when theme strength changes.

    Args:
        theme_data: Theme update dictionary
    """
    message = {
        "type": "theme_update",
        "timestamp": theme_data.get("updated_at"),
        "data": {
            "theme_name": theme_data.get("name"),
            "conviction": theme_data.get("conviction"),
            "evidence_count": theme_data.get("evidence_count")
        }
    }
    await manager.broadcast(message)


async def broadcast_high_conviction_alert(alert_data: dict):
    """
    Broadcast when new idea crosses high-conviction threshold (>=7/14).

    Args:
        alert_data: Alert data dictionary
    """
    message = {
        "type": "high_conviction_alert",
        "timestamp": alert_data.get("scored_at"),
        "data": {
            "theme": alert_data.get("theme_name"),
            "score": alert_data.get("total_score"),
            "sentiment": alert_data.get("sentiment")
        }
    }
    await manager.broadcast(message)


async def broadcast_synthesis_complete(synthesis_data: dict):
    """
    Broadcast when synthesis generation completes.

    Args:
        synthesis_data: Synthesis result dictionary
    """
    message = {
        "type": "synthesis_complete",
        "timestamp": synthesis_data.get("generated_at"),
        "data": {
            "status": synthesis_data.get("status"),
            "synthesis_id": synthesis_data.get("synthesis_id"),
            "time_window": synthesis_data.get("time_window"),
            "content_count": synthesis_data.get("content_count"),
            "error": synthesis_data.get("error")
        }
    }
    await manager.broadcast(message)
