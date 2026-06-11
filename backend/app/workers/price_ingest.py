"""Price ingestion worker — fetches real-time prices and forward curves."""

import json
import asyncio
from app.workers.celery_app import celery_app
from app.adapters import registry, register_all_adapters
from app.cache.redis_cache import RedisCache
import structlog

logger = structlog.get_logger()


def _get_cache():
    cache = RedisCache()
    loop = asyncio.new_event_loop()
    loop.run_until_complete(cache.connect())
    return cache, loop


@celery_app.task(name="app.workers.price_ingest.fetch_realtime")
def fetch_realtime():
    """Fetch real-time ticker prices and publish to WebSocket channel."""
    cache, loop = _get_cache()
    try:
        register_all_adapters()
        result = loop.run_until_complete(
            registry.fetch_with_fallback("realtime_prices", {"type": "tickers"})
        )
        if result.data:
            # Cache for API
            loop.run_until_complete(cache.set("tickers:latest", {
                "items": result.data,
                "_status": result.status.value,
                "_source": result.source_name,
                "_fetched_at": result.fetched_at.isoformat(),
            }, ttl_seconds=30))

            # Publish to WebSocket channel
            loop.run_until_complete(cache.publish("ws:tickers", {
                "type": "tickers", "data": result.data,
            }))
            logger.info("price_ingest_success", count=len(result.data), status=result.status.value)
    except Exception as e:
        logger.error("price_ingest_error", error=str(e))
    finally:
        loop.run_until_complete(cache.close())
        loop.close()


@celery_app.task(name="app.workers.price_ingest.fetch_forward_curves")
def fetch_forward_curves():
    """Fetch forward curves for WTI and Brent."""
    cache, loop = _get_cache()
    try:
        register_all_adapters()
        for commodity in ["wti", "brent"]:
            result = loop.run_until_complete(
                registry.fetch_with_fallback("forward_curves", {"type": "forward_curve", "commodity": commodity, "months": 35})
            )
            if result.data:
                loop.run_until_complete(cache.set(f"fwd_curve:{commodity}", {
                    "items": result.data,
                    "_status": result.status.value,
                    "_source": result.source_name,
                    "_fetched_at": result.fetched_at.isoformat(),
                }, ttl_seconds=60))
                logger.info("fwd_curve_ingest_success", commodity=commodity)
    except Exception as e:
        logger.error("fwd_curve_ingest_error", error=str(e))
    finally:
        loop.run_until_complete(cache.close())
        loop.close()
