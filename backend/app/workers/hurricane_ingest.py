"""Hurricane data ingestion worker."""

import asyncio
from app.workers.celery_app import celery_app
from app.adapters import registry, register_all_adapters
from app.cache.redis_cache import RedisCache
import structlog

logger = structlog.get_logger()


@celery_app.task(name="app.workers.hurricane_ingest.fetch_active")
def fetch_active():
    """Fetch active storms from NHC and publish to WebSocket."""
    cache = RedisCache()
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(cache.connect())
        register_all_adapters()
        result = loop.run_until_complete(
            registry.fetch_with_fallback("hurricane_data", {})
        )
        if result.data:
            loop.run_until_complete(cache.set("hurricanes:active", {
                **result.data,
                "_status": result.status.value,
                "_source": result.source_name,
                "_fetched_at": result.fetched_at.isoformat(),
            }, ttl_seconds=300))
            loop.run_until_complete(cache.publish("ws:hurricanes", {
                "type": "hurricanes", "data": result.data,
            }))
            logger.info("hurricane_ingest_success", count=result.data.get("count", 0))
    except Exception as e:
        logger.error("hurricane_ingest_error", error=str(e))
    finally:
        loop.run_until_complete(cache.close())
        loop.close()
