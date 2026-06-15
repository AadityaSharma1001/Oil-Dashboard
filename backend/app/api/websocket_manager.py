"""WebSocket connection manager with room-based pub/sub relay."""

import json
import asyncio
from collections import defaultdict
from typing import Optional
import structlog
from fastapi import WebSocket, WebSocketDisconnect
from app.observability.metrics import WS_CONNECTIONS, WS_MESSAGES_SENT

logger = structlog.get_logger()

ALLOWED_ROOMS = {"tickers", "intraday:wti", "intraday:brent", "alerts", "hurricanes", "trading"}


class ConnectionManager:
    """Manages WebSocket connections grouped by room (topic)."""

    def __init__(self):
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)
        self._redis = None

    def set_redis(self, redis_client):
        self._redis = redis_client

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        self._rooms[room].add(websocket)
        WS_CONNECTIONS.labels(room=room).inc()
        logger.info("ws_connected", room=room, total=len(self._rooms[room]))

    def disconnect(self, websocket: WebSocket, room: str):
        self._rooms[room].discard(websocket)
        WS_CONNECTIONS.labels(room=room).dec()
        logger.info("ws_disconnected", room=room, total=len(self._rooms[room]))

    async def broadcast(self, room: str, message: dict):
        """Send message to all connections in a room."""
        dead = []
        for ws in self._rooms.get(room, set()):
            try:
                await ws.send_json(message)
                WS_MESSAGES_SENT.labels(room=room).inc()
            except (WebSocketDisconnect, RuntimeError):
                dead.append(ws)
        for ws in dead:
            self._rooms[room].discard(ws)

    async def start_redis_listener(self):
        """Subscribe to Redis pub/sub channels and relay to WebSocket rooms."""
        if not self._redis:
            logger.warning("ws_redis_not_configured")
            return

        pubsub = self._redis.pubsub()
        channels = [f"ws:{room}" for room in ALLOWED_ROOMS]
        await pubsub.subscribe(*channels)
        logger.info("ws_redis_listener_started", channels=channels)

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"]
                    if isinstance(channel, bytes):
                        channel = channel.decode()
                    room = channel.replace("ws:", "")
                    try:
                        data = json.loads(message["data"])
                        await self.broadcast(room, data)
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning("ws_relay_parse_error", error=str(e))
        except asyncio.CancelledError:
            logger.info("ws_redis_listener_stopped")
        finally:
            await pubsub.unsubscribe(*channels)

    @property
    def total_connections(self) -> int:
        return sum(len(conns) for conns in self._rooms.values())

    def room_counts(self) -> dict[str, int]:
        return {room: len(conns) for room, conns in self._rooms.items() if conns}


# Global singleton
ws_manager = ConnectionManager()
