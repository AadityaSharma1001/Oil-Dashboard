"""News and sentiment ingestion worker — OilPrice + FinBERT."""

import asyncio
from app.workers.celery_app import celery_app
from app.adapters import registry, register_all_adapters
from app.cache.redis_cache import RedisCache
import structlog

logger = structlog.get_logger()


@celery_app.task(name="app.workers.news_ingest.fetch_and_score")
def fetch_and_score():
    """Fetch news from OilPrice, score with FinBERT, and cache."""
    cache = RedisCache()
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(cache.connect())
        register_all_adapters()

        # 1. Fetch news
        news_result = loop.run_until_complete(
            registry.fetch_with_fallback("news_data", {"type": "news"})
        )
        articles = news_result.data if isinstance(news_result.data, list) else []

        if articles:
            # 2. Score with FinBERT
            headlines = [a.get("headline", "") for a in articles if a.get("headline")]
            if headlines:
                sentiment_result = loop.run_until_complete(
                    registry.fetch_with_fallback("sentiment", {"texts": headlines})
                )
                s_data = sentiment_result.data or {}
                results = s_data.get("results", [])
                for i, art in enumerate(articles):
                    if i < len(results):
                        art["finbert_label"] = results[i].get("label", "neutral")
                        art["finbert_score"] = results[i].get("score", 0)
                        art["finbert_compound"] = results[i].get("compound", 0)
                        art["impact_score"] = int(results[i].get("compound", 0) * 10)

            # 3. Cache scored articles
            loop.run_until_complete(cache.set("news:scored", articles, ttl_seconds=900))
            logger.info("news_ingest_success", articles=len(articles))

    except Exception as e:
        logger.error("news_ingest_error", error=str(e))
    finally:
        loop.run_until_complete(cache.close())
        loop.close()
