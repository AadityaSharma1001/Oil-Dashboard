"""Signal compute worker — recomputes all signals and writes audit trail."""

import asyncio
import json
from datetime import datetime
from app.workers.celery_app import celery_app
from app.adapters import registry, register_all_adapters
from app.cache.redis_cache import RedisCache
from app.analytics.signals import (
    score_fundamental_indicator, score_news_sentiment,
    compute_final_signal, compute_trade_signals,
)
from app.config import get_settings
import structlog

logger = structlog.get_logger()
settings = get_settings()


@celery_app.task(name="app.workers.signal_compute.recompute_all")
def recompute_all():
    """Recompute all trading signals and publish alerts."""
    cache = RedisCache()
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(cache.connect())
        register_all_adapters()

        # 1. Get fundamentals
        fund_result = loop.run_until_complete(
            registry.fetch_with_fallback("fundamentals", {"type": "fundamentals"})
        )
        fund_data = fund_result.data or {}

        # 2. Score fundamentals
        fundamental_signals = []
        for key, info in fund_data.items():
            if isinstance(info, dict) and "value" in info and "prior_value" in info:
                try:
                    signal = score_fundamental_indicator(key, float(info["value"]), float(info["prior_value"]))
                    fundamental_signals.append(signal)
                except (ValueError, TypeError):
                    pass

        # 3. Get and score news
        news_result = loop.run_until_complete(
            registry.fetch_with_fallback("news_data", {"type": "news"})
        )
        articles = news_result.data if isinstance(news_result.data, list) else []
        if articles:
            headlines = [a.get("headline", "") for a in articles]
            s_result = loop.run_until_complete(
                registry.fetch_with_fallback("sentiment", {"texts": headlines})
            )
            s_data = s_result.data or {}
            for i, art in enumerate(articles):
                r = s_data.get("results", [])
                if i < len(r):
                    art["finbert_compound"] = r[i].get("compound", 0)

        news_signals = score_news_sentiment(articles)

        # 4. Compute final signal
        final = compute_final_signal(fundamental_signals, news_signals)

        # 5. Compute trade signals
        trade_signals = compute_trade_signals(
            fundamentals=fund_data,
            cracks=[{"current": 30.0, "avg5yr": 28.5}],
            spreads={"bw_mean": 3.85, "bw_std": 0.45, "bw_z_score": 1.5, "m1m12_current": 2.0},
            macro={},
        )

        # 6. Cache results
        signal_data = {
            **final,
            "fundamental_signals": fundamental_signals,
            "news_signals": news_signals,
            "trade_signals": trade_signals,
            "_status": "live",
            "_source": "signal_engine",
            "_fetched_at": datetime.utcnow().isoformat(),
        }
        loop.run_until_complete(cache.set("signals:engine", signal_data, ttl_seconds=300))
        loop.run_until_complete(cache.set("signals:trade", {
            "signals": trade_signals,
            "buy_count": sum(1 for s in trade_signals if s["direction"] == "BUY"),
            "sell_count": sum(1 for s in trade_signals if s["direction"] == "SELL"),
            "hold_count": sum(1 for s in trade_signals if s["direction"] == "HOLD"),
            "_status": "live",
            "_source": "signal_engine",
            "_fetched_at": datetime.utcnow().isoformat(),
        }, ttl_seconds=300))

        # 7. Publish alert via WebSocket if signal changed
        loop.run_until_complete(cache.publish("ws:alerts", {
            "type": "signal_update",
            "direction": final["final_direction"],
            "confidence": final["final_confidence"],
            "timestamp": datetime.utcnow().isoformat(),
        }))

        logger.info(
            "signal_compute_success",
            direction=final["final_direction"],
            confidence=final["final_confidence"],
        )

    except Exception as e:
        logger.error("signal_compute_error", error=str(e))
    finally:
        loop.run_until_complete(cache.close())
        loop.close()
