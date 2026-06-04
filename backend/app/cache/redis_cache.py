"""Redis cache layer with TTL management and pub/sub for WebSocket broadcast.
Gracefully degrades to no-cache mode when Redis is unavailable."""

import json
import time
from typing import Any, Optional
from datetime import datetime
import redis.asyncio as redis
from app.config import get_settings
import structlog

logger = structlog.get_logger()
settings = get_settings()


class RedisCache:
    """Async Redis cache with graceful degradation when Redis is offline."""

    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._available: bool = False

    async def connect(self):
        try:
            self._redis = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
            )
            await self._redis.ping()
            self._available = True
            logger.info("redis_connected")
        except Exception as e:
            self._available = False
            logger.warning("redis_unavailable_running_without_cache", error=str(e))

    async def close(self):
        if self._redis:
            try:
                await self._redis.close()
            except Exception:
                pass

    @property
    def client(self) -> Optional[redis.Redis]:
        return self._redis if self._available else None

    async def get(self, key: str) -> Optional[dict]:
        if not self._available:
            return None
        try:
            raw = await self._redis.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception:
            return None

    async def get_with_age(self, key: str) -> tuple[Optional[dict], Optional[float]]:
        if not self._available:
            return None, None
        try:
            pipe = self._redis.pipeline()
            pipe.get(key)
            pipe.get(f"{key}:ts")
            raw, ts_raw = await pipe.execute()
            if raw is None:
                return None, None
            data = json.loads(raw)
            age = None
            if ts_raw:
                try:
                    age = time.time() - float(ts_raw)
                except (ValueError, TypeError):
                    pass
            return data, age
        except Exception:
            return None, None

    async def set(self, key: str, value: Any, ttl_seconds: int = 60):
        if not self._available:
            return
        try:
            serialized = json.dumps(value, default=str)
            pipe = self._redis.pipeline()
            pipe.set(key, serialized, ex=ttl_seconds)
            pipe.set(f"{key}:ts", str(time.time()), ex=ttl_seconds)
            await pipe.execute()
        except Exception:
            pass

    async def delete(self, key: str):
        if not self._available:
            return
        try:
            pipe = self._redis.pipeline()
            pipe.delete(key)
            pipe.delete(f"{key}:ts")
            await pipe.execute()
        except Exception:
            pass

    async def publish(self, channel: str, message: dict):
        if not self._available:
            return
        try:
            await self._redis.publish(channel, json.dumps(message, default=str))
        except Exception:
            pass

    async def health_check(self) -> bool:
        if not self._available:
            return False
        try:
            return await self._redis.ping()
        except Exception:
            self._available = False
            return False


# Global singleton
cache = RedisCache()
