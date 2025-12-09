"""WebSocket handler for generation progress updates."""

from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

router = APIRouter()


class ProgressConnectionManager:
    """Manages WebSocket connections for progress updates."""

    def __init__(self):
        # job_id -> set of websocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        """Accept and track a new WebSocket connection."""
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()
        self.active_connections[job_id].add(websocket)

    def disconnect(self, websocket: WebSocket, job_id: str):
        """Remove a WebSocket connection."""
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

    async def broadcast_to_job(self, job_id: str, message: dict):
        """Broadcast a message to all connections watching a job."""
        if job_id not in self.active_connections:
            return

        dead_connections = []
        for connection in self.active_connections[job_id]:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)

        # Clean up dead connections
        for conn in dead_connections:
            self.active_connections[job_id].discard(conn)

    def get_connection_count(self, job_id: str) -> int:
        """Get the number of connections watching a job."""
        return len(self.active_connections.get(job_id, set()))


# Global connection manager instance
progress_manager = ProgressConnectionManager()


async def broadcast_progress(job_id: str, progress_data: dict):
    """
    Broadcast progress update to all connected clients.
    Called from Celery tasks via Redis pub/sub.
    """
    await progress_manager.broadcast_to_job(job_id, {
        "type": "progress",
        "data": progress_data,
    })


@router.websocket("/progress/{job_id}")
async def progress_websocket(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for receiving generation progress updates.

    Messages sent to client:
    - {"type": "progress", "data": {...}}  # Progress updates
    - {"type": "completed", "data": {...}} # Generation completed
    - {"type": "error", "data": {...}}     # Error occurred

    Messages from client:
    - "ping" -> responds with "pong"
    """
    await progress_manager.connect(websocket, job_id)

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "job_id": job_id,
        })

        while True:
            # Keep connection alive, handle client messages
            data = await websocket.receive_text()

            if data == "ping":
                await websocket.send_text("pong")
            elif data == "status":
                # Client requesting current status
                # In production, would fetch from database
                await websocket.send_json({
                    "type": "status_response",
                    "job_id": job_id,
                    "connections": progress_manager.get_connection_count(job_id),
                })

    except WebSocketDisconnect:
        progress_manager.disconnect(websocket, job_id)
    except Exception:
        progress_manager.disconnect(websocket, job_id)
