"""API dependencies — Redis cache, adapter registry, DB session."""

from app.cache import cache
from app.adapters import registry
from app.api.websocket_manager import ws_manager
