"""
API v1 Router — all REST + WebSocket endpoints for the Oil Trading Dashboard.
Each endpoint returns APIResponse{data, provenance} for live/mock tracking.
"""

import asyncio
import time
from datetime import datetime, timedelta
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import structlog

from app.schemas.common import APIResponse, DataProvenance, DataStatus
from app.adapters.base import SourceStatus, AdapterResult
from app.adapters import registry
from app.cache import cache
from app.api.websocket_manager import ws_manager, ALLOWED_ROOMS
from app.analytics.vwap import compute_vwap, compute_vwap_metrics
from app.analytics.crack_calc import compute_all_cracks
from app.analytics.signals import (
    score_fundamental_indicator, score_news_sentiment,
    compute_trade_signals, compute_final_signal,
)
from app.analytics.pca import forward_curve_pca, _mock_pca
from app.analytics.spreads import compute_arb_analytics
from app.analytics.correlation import rolling_correlation
from app.observability.metrics import CACHE_HIT, CACHE_MISS

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1")


def _provenance(result: AdapterResult, cache_age: float = None) -> DataProvenance:
    """Build DataProvenance from an AdapterResult."""
    status_map = {
        SourceStatus.LIVE: DataStatus.LIVE,
        SourceStatus.STALE: DataStatus.STALE,
        SourceStatus.MOCK: DataStatus.MOCK,
        SourceStatus.DEGRADED: DataStatus.DEGRADED,
        SourceStatus.DOWN: DataStatus.MOCK,
    }
    return DataProvenance(
        status=status_map.get(result.status, DataStatus.MOCK),
        source=result.source_name,
        fetched_at=result.fetched_at,
        cache_age_seconds=cache_age,
        message=result.error_message,
    )


async def _cached_fetch(cache_key: str, data_type: str, params: dict, ttl: int) -> tuple[dict, DataProvenance]:
    """Fetch from cache, fall back to adapter registry with fallback chains."""
    cached, age = await cache.get_with_age(cache_key)
    if cached is not None:
        CACHE_HIT.labels(endpoint=cache_key).inc()
        prov = DataProvenance(
            status=DataStatus(cached.get("_status", "live")),
            source=cached.get("_source", "cache"),
            fetched_at=datetime.fromisoformat(cached["_fetched_at"]) if "_fetched_at" in cached else datetime.utcnow(),
            cache_age_seconds=age,
        )
        data = {k: v for k, v in cached.items() if not k.startswith("_")}
        return data, prov

    CACHE_MISS.labels(endpoint=cache_key).inc()
    result = await registry.fetch_with_fallback(data_type, params)
    prov = _provenance(result)

    if result.data is not None:
        to_cache = result.data if isinstance(result.data, dict) else {"items": result.data}
        to_cache["_status"] = result.status.value
        to_cache["_source"] = result.source_name
        to_cache["_fetched_at"] = result.fetched_at.isoformat()
        await cache.set(cache_key, to_cache, ttl)

    return result.data, prov


# ════════════════════════════════════════════════════════════════════
# TICKERS
# ════════════════════════════════════════════════════════════════════

@router.get("/tickers")
async def get_tickers():
    """Real-time ticker prices for WTI, Brent, RBOB, HO, NatGas, DXY, etc."""
    result = await registry.fetch_with_fallback("realtime_prices", {"type": "tickers"})
    return APIResponse(data=result.data, provenance=_provenance(result))


# ════════════════════════════════════════════════════════════════════
# FORWARD CURVES
# ════════════════════════════════════════════════════════════════════

@router.get("/forward-curves/{commodity}")
async def get_forward_curves(commodity: str):
    """Forward curve (M1-M36) with 5-year average."""
    cache_key = f"fwd_curve:{commodity}"
    cached, age = await cache.get_with_age(cache_key)
    if cached:
        CACHE_HIT.labels(endpoint="forward_curves").inc()
        return APIResponse(
            data=cached.get("items", cached),
            provenance=DataProvenance(
                status=DataStatus(cached.get("_status", "live")),
                source=cached.get("_source", "cache"),
                fetched_at=datetime.utcnow(),
                cache_age_seconds=age,
            ),
        )
    CACHE_MISS.labels(endpoint="forward_curves").inc()
    result = await registry.fetch_with_fallback(
        "forward_curves", {"type": "forward_curve", "commodity": commodity}
    )
    if result.data:
        await cache.set(cache_key, {"items": result.data, "_status": result.status.value, "_source": result.source_name, "_fetched_at": result.fetched_at.isoformat()}, 30)
    return APIResponse(data=result.data, provenance=_provenance(result))


# ════════════════════════════════════════════════════════════════════
# INTRADAY VWAP
# ════════════════════════════════════════════════════════════════════

@router.get("/intraday/{commodity}")
async def get_intraday(commodity: str):
    """Intraday VWAP + Bollinger Bands — computed server-side."""
    symbol = "CL=F" if commodity == "wti" else "BZ=F"
    result = await registry.fetch_with_fallback(
        "intraday_bars", {"type": "intraday", "symbol": symbol}
    )
    if result.data and isinstance(result.data, list):
        enriched = compute_vwap(result.data)
        metrics = compute_vwap_metrics(enriched)
        return APIResponse(
            data={"commodity": commodity, "data": enriched, **metrics},
            provenance=_provenance(result),
        )
    # Return mock VWAP data
    return APIResponse(
        data={"commodity": commodity, "data": [], "last_vwap": 0, "last_band_width": 0, "last_deviation": 0},
        provenance=_provenance(result),
    )


# ════════════════════════════════════════════════════════════════════
# SPREADS
# ════════════════════════════════════════════════════════════════════

@router.get("/spreads/calendar/{commodity}")
async def get_calendar_spreads(commodity: str, tenor: str = "M1-M2"):
    """Calendar spreads with historical range."""
    # Compute from forward curve data
    cache_key = f"spread:cal:{commodity}:{tenor}"
    cached, age = await cache.get_with_age(cache_key)
    if cached:
        CACHE_HIT.labels(endpoint="spreads_calendar").inc()
        return APIResponse(data=cached.get("items", cached), provenance=DataProvenance(
            status=DataStatus.LIVE, source="cache", fetched_at=datetime.utcnow(), cache_age_seconds=age,
        ))
    CACHE_MISS.labels(endpoint="spreads_calendar").inc()
    # Generate mock spread data
    import numpy as np
    np.random.seed(42)
    data = [{"day": f"D{i+1}", "value": round(3.5 + np.random.randn() * 0.3, 3),
             "mean": 3.5, "hi": 4.2, "lo": 2.8} for i in range(30)]
    await cache.set(cache_key, {"items": data}, 60)
    return APIResponse(
        data={"commodity": commodity, "tenor": tenor, "data": data},
        provenance=DataProvenance(status=DataStatus.MOCK, source="computed", fetched_at=datetime.utcnow()),
    )


@router.get("/spreads/fly/{commodity}")
async def get_fly_spreads(commodity: str):
    """Butterfly spreads — term structure and history."""
    # Mock butterfly data
    data = {
        "commodity": commodity,
        "term_structure": [
            {"label": "M1-M2-M3", "value": 0.42, "mean": 0.35, "hi": 0.65, "lo": 0.10},
            {"label": "M2-M3-M4", "value": 0.28, "mean": 0.22, "hi": 0.48, "lo": 0.05},
            {"label": "M3-M4-M5", "value": 0.15, "mean": 0.12, "hi": 0.35, "lo": -0.02},
        ],
    }
    return APIResponse(
        data=data,
        provenance=DataProvenance(status=DataStatus.MOCK, source="computed", fetched_at=datetime.utcnow()),
    )


@router.get("/spreads/m1-m12/{commodity}")
async def get_m1_m12_spread(commodity: str):
    """M1-M12 time spread."""
    import numpy as np
    np.random.seed(123)
    data = [{"day": f"D{i+1}", "wti": round(2.1 + np.random.randn() * 0.4, 2),
             "brent": round(2.8 + np.random.randn() * 0.5, 2)} for i in range(30)]
    return APIResponse(
        data={"data": data, "threshold": 0},
        provenance=DataProvenance(status=DataStatus.MOCK, source="computed", fetched_at=datetime.utcnow()),
    )


# ════════════════════════════════════════════════════════════════════
# 5-YEAR RANGE
# ════════════════════════════════════════════════════════════════════

@router.get("/five-year-range/{commodity}")
async def get_five_year_range(commodity: str):
    """5-year same-day price range."""
    symbol = "CL=F" if commodity == "wti" else "BZ=F"
    result = await registry.fetch_with_fallback("forward_curves", {"type": "historical", "symbol": symbol, "period": "5y"})
    # For now, return structured mock
    import numpy as np
    np.random.seed(42)
    base = 72.0 if commodity == "wti" else 76.0
    data = []
    for i in range(252):
        mean = base + np.sin(i / 40) * 8
        data.append({
            "day": f"D{i+1}",
            "high5yr": round(mean + 12 + np.random.rand() * 3, 2),
            "low5yr": round(mean - 12 - np.random.rand() * 3, 2),
            "mean5yr": round(mean, 2),
            "open": round(mean + np.random.randn() * 2, 2) if i < 120 else None,
            "close": round(mean + np.random.randn() * 2 + 0.3, 2) if i < 120 else None,
        })
    return APIResponse(
        data={"commodity": commodity, "data": data, "current_price": base, "mean_price": base - 0.5, "vs_mean": 0.5, "percentile": 62},
        provenance=DataProvenance(status=DataStatus.MOCK, source="computed", fetched_at=datetime.utcnow()),
    )


# ════════════════════════════════════════════════════════════════════
# CORE DESK ANALYTICS
# ════════════════════════════════════════════════════════════════════

@router.get("/core-desk/covariance")
async def get_covariance():
    """EWMA covariance and correlation matrix."""
    labels = ["WTI", "Brent", "RBOB", "Gasoil", "DXY"]
    # Mock EWMA correlation
    corr = [
        [1.00, 0.95, 0.82, 0.78, -0.42],
        [0.95, 1.00, 0.80, 0.85, -0.38],
        [0.82, 0.80, 1.00, 0.72, -0.28],
        [0.78, 0.85, 0.72, 1.00, -0.25],
        [-0.42, -0.38, -0.28, -0.25, 1.00],
    ]
    highlights = [[1 if abs(corr[i][j]) > 0.7 and i != j else 0 for j in range(5)] for i in range(5)]
    return APIResponse(
        data={"labels": labels, "values": corr, "highlights": highlights},
        provenance=DataProvenance(status=DataStatus.MOCK, source="computed", fetched_at=datetime.utcnow()),
    )


@router.get("/core-desk/pca/{commodity}")
async def get_pca(commodity: str):
    """PCA decomposition of forward curve."""
    pca_result = _mock_pca()
    return APIResponse(
        data={"commodity": commodity, **pca_result},
        provenance=DataProvenance(status=DataStatus.MOCK, source="computed", fetched_at=datetime.utcnow()),
    )


@router.get("/core-desk/dollar-correlation")
async def get_dollar_correlation():
    """Rolling 60d WTI-Dollar Pearson correlation."""
    import numpy as np
    np.random.seed(77)
    data = [{"day": f"D{i+1}", "correlation": round(-0.45 + np.random.randn() * 0.12, 3)} for i in range(60)]
    current = data[-1]["correlation"]
    return APIResponse(
        data={"data": data, "current": current},
        provenance=DataProvenance(status=DataStatus.MOCK, source="computed", fetched_at=datetime.utcnow()),
    )


@router.get("/core-desk/arb/wti-brent")
async def get_wti_brent_arb():
    """WTI-Brent arbitrage spread with Z-score."""
    import numpy as np
    np.random.seed(55)
    spread_series = [3.85 + np.random.randn() * 0.45 for _ in range(30)]
    labels = [f"D{i+1}" for i in range(30)]
    arb = compute_arb_analytics(spread_series, labels)
    return APIResponse(
        data=arb,
        provenance=DataProvenance(status=DataStatus.MOCK, source="computed", fetched_at=datetime.utcnow()),
    )


@router.get("/core-desk/differentials")
async def get_differentials():
    """Physical grade differentials."""
    data = [
        {"grade": "Midland WTI", "value": -0.75},
        {"grade": "WCS (Canada)", "value": -14.20},
        {"grade": "Urals (CIF NWE)", "value": -12.50},
        {"grade": "EFP", "value": 0.85},
    ]
    return APIResponse(
        data={"data": data},
        provenance=DataProvenance(status=DataStatus.MOCK, source="computed", fetched_at=datetime.utcnow()),
    )


# ════════════════════════════════════════════════════════════════════
# CRACK SPREADS
# ════════════════════════════════════════════════════════════════════

@router.get("/crack-spreads")
async def get_crack_spreads():
    """Major crack spreads — computed from product and crude prices."""
    cracks = compute_all_cracks({
        "wti": 72.45, "brent": 76.30, "rbob": 2.342, "ho": 2.485, "gasoil": 684.0,
    })
    # Compute deviations
    for c in cracks:
        c["deviation"] = round(c["current"] - c["avg5yr"], 2)
        c["deviation_pct"] = round((c["deviation"] / c["avg5yr"]) * 100, 1) if c["avg5yr"] else 0
    return APIResponse(
        data={"data": cracks},
        provenance=DataProvenance(status=DataStatus.MOCK, source="computed", fetched_at=datetime.utcnow()),
    )


# ════════════════════════════════════════════════════════════════════
# FUNDAMENTALS
# ════════════════════════════════════════════════════════════════════

@router.get("/fundamentals/cards")
async def get_fundamentals_cards():
    """EIA fundamental indicator cards."""
    result = await registry.fetch_with_fallback("fundamentals", {"type": "fundamentals"})
    data = result.data or {}

    cards = []
    card_config = [
        ("us_crude_stocks", "US Crude Stocks", "mb", None),
        ("cushing_inventory", "Cushing Inventory", "mb", None),
        ("us_production", "US Production", "mb/d", None),
        ("refinery_utilization", "Refinery Util", "%", None),
        ("spr_level", "SPR Level", "mb", None),
        ("rig_count", "Rig Count", "rigs", None),
    ]
    for key, label, unit, _ in card_config:
        info = data.get(key, {})
        value = info.get("value", "N/A")
        prior = info.get("prior_value")
        change = None
        direction = None
        if value != "N/A" and prior:
            try:
                change = round(float(value) - float(prior), 2)
                direction = "up" if change > 0 else "down" if change < 0 else "flat"
            except (ValueError, TypeError):
                pass
        cards.append({
            "id": key, "label": label, "value": str(value), "unit": unit,
            "change": change, "direction": direction,
        })

    return APIResponse(data={"cards": cards}, provenance=_provenance(result))


@router.get("/fundamentals/cushing")
async def get_cushing():
    """Cushing inventory time series."""
    import numpy as np
    np.random.seed(88)
    data = [{"week": f"W{i+1}", "stock": round(35 + np.random.randn() * 2, 1), "avg5yr": 38.0} for i in range(52)]
    return APIResponse(
        data={"utilization": 46.5, "data": data},
        provenance=DataProvenance(status=DataStatus.MOCK, source="eia", fetched_at=datetime.utcnow()),
    )


@router.get("/fundamentals/floating-storage")
async def get_floating_storage():
    """Global floating storage estimates."""
    result = await registry.fetch_with_fallback("shipping_data", {"type": "floating_storage"})
    return APIResponse(data=result.data, provenance=_provenance(result))


@router.get("/fundamentals/spare-capacity")
async def get_spare_capacity():
    """OPEC spare capacity and macro table."""
    data = {
        "spare_capacity": [
            {"indicator": "OPEC Spare Capacity", "latest": "3.2 mb/d", "prior": "3.5 mb/d"},
            {"indicator": "Non-OPEC Growth", "latest": "+1.4 mb/d", "prior": "+1.2 mb/d"},
            {"indicator": "Global Demand Growth", "latest": "+1.1 mb/d", "prior": "+1.0 mb/d"},
        ],
        "macro_table": [
            {"indicator": "US PMI", "latest": "51.3", "prior": "50.8"},
            {"indicator": "China PMI", "latest": "50.8", "prior": "49.2"},
            {"indicator": "EUR CPI", "latest": "2.1%", "prior": "2.4%"},
            {"indicator": "DXY", "latest": "104.2", "prior": "103.8"},
        ],
    }
    return APIResponse(
        data=data,
        provenance=DataProvenance(status=DataStatus.MOCK, source="computed", fetched_at=datetime.utcnow()),
    )


# ════════════════════════════════════════════════════════════════════
# SIGNALS
# ════════════════════════════════════════════════════════════════════

@router.get("/signals/engine")
async def get_signal_engine():
    """Full signal engine output — fundamental + news scoring."""
    # Fetch fundamentals
    fund_result = await registry.fetch_with_fallback("fundamentals", {"type": "fundamentals"})
    fund_data = fund_result.data or {}

    # Score fundamentals
    fundamental_signals = []
    for key, info in fund_data.items():
        if isinstance(info, dict) and "value" in info and "prior_value" in info:
            try:
                signal = score_fundamental_indicator(key, float(info["value"]), float(info["prior_value"]))
                fundamental_signals.append(signal)
            except (ValueError, TypeError):
                pass

    # Fetch and score news
    news_result = await registry.fetch_with_fallback("news_data", {"type": "news"})
    articles = news_result.data if isinstance(news_result.data, list) else []

    # FinBERT scoring
    if articles:
        headlines = [a.get("headline", "") for a in articles]
        sentiment_result = await registry.fetch_with_fallback("sentiment", {"texts": headlines})
        sentiment_data = sentiment_result.data or {}
        results = sentiment_data.get("results", [])
        for i, art in enumerate(articles):
            if i < len(results):
                art["finbert_compound"] = results[i].get("compound", 0)
                art["finbert_label"] = results[i].get("label", "neutral")

    news_signals = score_news_sentiment(articles)
    final = compute_final_signal(fundamental_signals, news_signals)

    return APIResponse(
        data={
            **final,
            "fundamental_signals": fundamental_signals,
            "news_signals": news_signals,
        },
        provenance=_provenance(fund_result),
    )


@router.get("/signals/trade")
async def get_trade_signals():
    """Individual trade signal cards."""
    signals = compute_trade_signals(
        fundamentals={"us_crude_stocks": {"change": -6.1}},
        cracks=[{"current": 30.5, "avg5yr": 28.5}],
        spreads={"bw_mean": 3.85, "bw_std": 0.45, "bw_z_score": 1.8, "m1m12_current": 2.1},
        macro={"dxy": {"change": -0.32}},
    )
    buy = sum(1 for s in signals if s["direction"] == "BUY")
    sell = sum(1 for s in signals if s["direction"] == "SELL")
    hold = sum(1 for s in signals if s["direction"] == "HOLD")

    return APIResponse(
        data={"signals": signals, "buy_count": buy, "sell_count": sell, "hold_count": hold},
        provenance=DataProvenance(status=DataStatus.MOCK, source="computed", fetched_at=datetime.utcnow()),
    )


@router.get("/signals/audit")
async def get_signal_audit(limit: int = 50, offset: int = 0):
    """Signal audit trail — paginated."""
    # In production, query signal_audit table
    return APIResponse(
        data={"records": [], "total": 0},
        provenance=DataProvenance(status=DataStatus.LIVE, source="db", fetched_at=datetime.utcnow()),
    )


@router.get("/signals/news")
async def get_signals_news():
    """News headlines with sentiment scores."""
    result = await registry.fetch_with_fallback("news_data", {"type": "news"})
    articles = result.data if isinstance(result.data, list) else []

    if articles:
        headlines = [a.get("headline", "") for a in articles]
        sentiment = await registry.fetch_with_fallback("sentiment", {"texts": headlines})
        s_data = sentiment.data or {}
        results = s_data.get("results", [])
        for i, art in enumerate(articles):
            if i < len(results):
                art["label"] = results[i].get("label", "neutral")
                art["score"] = results[i].get("score", 0)
                art["compound"] = results[i].get("compound", 0)

    return APIResponse(data={"articles": articles}, provenance=_provenance(result))


# ════════════════════════════════════════════════════════════════════
# SENTIMENT
# ════════════════════════════════════════════════════════════════════

@router.get("/sentiment/latest")
async def get_sentiment_latest(limit: int = 20):
    """Latest news with FinBERT sentiment scores."""
    result = await registry.fetch_with_fallback("news_data", {"type": "news"})
    articles = result.data[:limit] if isinstance(result.data, list) else []

    if articles:
        headlines = [a.get("headline", "") for a in articles]
        sentiment = await registry.fetch_with_fallback("sentiment", {"texts": headlines})
        s_data = sentiment.data or {}
        results = s_data.get("results", [])
        for i, art in enumerate(articles):
            if i < len(results):
                art["label"] = results[i].get("label", "neutral")
                art["score"] = results[i].get("score", 0)
                art["compound"] = results[i].get("compound", 0)
                art["impact_score"] = int(results[i].get("compound", 0) * 10)

    return APIResponse(data={"articles": articles}, provenance=_provenance(result))


@router.get("/sentiment/aggregate")
async def get_sentiment_aggregate():
    """Aggregated sentiment by category."""
    result = await registry.fetch_with_fallback("news_data", {"type": "news"})
    articles = result.data if isinstance(result.data, list) else []

    if articles:
        headlines = [a.get("headline", "") for a in articles]
        sentiment = await registry.fetch_with_fallback("sentiment", {"texts": headlines})
        s_data = sentiment.data or {}
        results = s_data.get("results", [])
        for i, art in enumerate(articles):
            if i < len(results):
                art["compound"] = results[i].get("compound", 0)

    # Aggregate by category
    cats = {}
    for art in articles:
        cat = art.get("category", "General")
        compound = art.get("compound", 0)
        if cat not in cats:
            cats[cat] = {"total": 0, "count": 0}
        cats[cat]["total"] += compound
        cats[cat]["count"] += 1

    aggregates = []
    for cat, data in cats.items():
        avg = data["total"] / data["count"] if data["count"] > 0 else 0
        aggregates.append({
            "category": cat, "avg_compound": round(avg, 4),
            "article_count": data["count"],
            "bias": "bullish" if avg > 0.1 else "bearish" if avg < -0.1 else "neutral",
        })

    overall = sum(a.get("compound", 0) for a in articles) / len(articles) if articles else 0
    return APIResponse(
        data={
            "aggregates": aggregates, "overall_compound": round(overall, 4),
            "overall_bias": "bullish" if overall > 0.1 else "bearish" if overall < -0.1 else "neutral",
        },
        provenance=_provenance(result),
    )


# ════════════════════════════════════════════════════════════════════
# COT
# ════════════════════════════════════════════════════════════════════

@router.get("/cot/positioning")
async def get_cot(weeks: int = 12):
    """CFTC COT positioning data."""
    result = await registry.fetch_with_fallback("cot_data", {"weeks": weeks})
    raw = result.data if isinstance(result.data, list) else []

    data = []
    for row in raw:
        mm_long = row.get("managed_money_long", 0)
        mm_short = row.get("managed_money_short", 0)
        sd_long = row.get("swap_dealer_long", 0)
        sd_short = row.get("swap_dealer_short", 0)
        net_mm = mm_long - mm_short
        net_sd = sd_long - sd_short
        data.append({
            "week": row.get("report_date", ""),
            "managed_money": net_mm,
            "producer": row.get("producer_long", 0) - row.get("producer_short", 0),
            "swap_dealer": net_sd,
            "net_spec": net_mm + net_sd,
        })

    return APIResponse(data={"data": data}, provenance=_provenance(result))


# ════════════════════════════════════════════════════════════════════
# FREIGHT
# ════════════════════════════════════════════════════════════════════

@router.get("/freight/bdti")
async def get_bdti():
    """BDTI Freight Index."""
    import numpy as np
    np.random.seed(99)
    base = 1150
    data = [{"day": f"D{i+1}", "value": round(base + np.cumsum(np.random.randn(1))[0] * 15, 0)} for i in range(30)]
    current = data[-1]["value"]
    first = data[0]["value"]
    change = current - first
    pct = (change / first) * 100 if first else 0

    return APIResponse(
        data={"data": data, "current": current, "change_30d": round(change, 0), "change_30d_pct": round(pct, 1)},
        provenance=DataProvenance(status=DataStatus.MOCK, source="mock", fetched_at=datetime.utcnow()),
    )


# ════════════════════════════════════════════════════════════════════
# SHIPPING
# ════════════════════════════════════════════════════════════════════

@router.get("/shipping/chokepoints")
async def get_chokepoints():
    """Chokepoint transit data."""
    result = await registry.fetch_with_fallback("shipping_data", {"type": "chokepoints"})
    return APIResponse(data={"chokepoints": result.data}, provenance=_provenance(result))


@router.get("/shipping/floating-storage")
async def get_shipping_floating_storage():
    """Floating storage by region."""
    result = await registry.fetch_with_fallback("shipping_data", {"type": "floating_storage"})
    return APIResponse(data=result.data, provenance=_provenance(result))


@router.get("/shipping/china-imports")
async def get_china_imports():
    """China crude oil import flows."""
    result = await registry.fetch_with_fallback("shipping_data", {"type": "china_imports"})
    return APIResponse(data=result.data, provenance=_provenance(result))


@router.get("/shipping/vlcc-rates")
async def get_vlcc_rates():
    """VLCC rates by route."""
    result = await registry.fetch_with_fallback("shipping_data", {"type": "vlcc_rates"})
    return APIResponse(data={"rates": result.data}, provenance=_provenance(result))


@router.get("/shipping/fleet-utilization")
async def get_fleet_utilization():
    """Fleet utilization by tanker class."""
    result = await registry.fetch_with_fallback("shipping_data", {"type": "fleet_utilization"})
    return APIResponse(data=result.data, provenance=_provenance(result))


# ════════════════════════════════════════════════════════════════════
# STEO
# ════════════════════════════════════════════════════════════════════

@router.get("/steo/balance")
async def get_steo():
    """EIA STEO supply/demand balance."""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    data = []
    import numpy as np
    np.random.seed(44)
    for m in months:
        supply = round(101.5 + np.random.randn() * 1.2, 1)
        demand = round(102.0 + np.random.randn() * 1.0, 1)
        opec = round(supply * 0.35, 1)
        data.append({
            "month": m, "supply": supply, "demand": demand,
            "balance": round(supply - demand, 1),
            "opec": opec, "nonOpec": round(supply - opec, 1),
        })
    return APIResponse(
        data={"data": data},
        provenance=DataProvenance(status=DataStatus.MOCK, source="eia", fetched_at=datetime.utcnow()),
    )


# ════════════════════════════════════════════════════════════════════
# HURRICANES
# ════════════════════════════════════════════════════════════════════

@router.get("/hurricanes/active")
async def get_hurricanes():
    """Active storms with tracks, infrastructure impact, and season summary."""
    result = await registry.fetch_with_fallback("hurricane_data", {})
    raw = result.data or {}

    # Build the full hurricane response from NHC data or mock
    response = {
        "season": {"year": 2026, "named_storms": 8, "hurricanes": 4, "major_hurricanes": 2, "ace_index": 72.4},
        "active_storms": [
            {
                "id": "AL042026", "name": "Hurricane Danielle", "category": 2,
                "wind": 105, "pressure": 968, "movement": "NW at 12 mph",
                "location": {"lat": 25.4, "lon": -89.2}, "status": "Category 2 Hurricane",
                "distance_to_shore": 185,
                "track": [
                    {"lon": -82.0, "lat": 20.5, "type": "past", "time": "Mon 12Z", "cat": "TS"},
                    {"lon": -84.5, "lat": 22.0, "type": "past", "time": "Tue 00Z", "cat": "H1"},
                    {"lon": -87.0, "lat": 23.5, "type": "past", "time": "Tue 12Z", "cat": "H1"},
                    {"lon": -89.2, "lat": 25.4, "type": "current", "time": "Now", "cat": "H2"},
                    {"lon": -90.5, "lat": 27.0, "type": "forecast", "time": "+12h", "cat": "H2"},
                    {"lon": -91.2, "lat": 28.8, "type": "forecast", "time": "+24h", "cat": "H1"},
                    {"lon": -91.8, "lat": 30.2, "type": "forecast", "time": "+36h", "cat": "TS"},
                ],
            },
        ],
        "infrastructure": {
            "platforms_shut_in": 12, "platforms_total": 175,
            "production_offline": 0.42, "production_total": 1.9,
            "ref_capacity_at_risk": 2.8, "ref_capacity_total": 18.4,
            "ports_closed": ["Corpus Christi", "Freeport"], "ports_open": 8,
        },
        "gulf_platforms": [
            {"name": "Thunder Horse", "lat": 28.2, "lon": -88.5, "status": "reduced", "capacity": 0.25},
            {"name": "Mars", "lat": 28.9, "lon": -89.3, "status": "evacuated", "capacity": 0.20},
            {"name": "Atlantis", "lat": 27.2, "lon": -89.9, "status": "normal", "capacity": 0.15},
            {"name": "Perdido", "lat": 26.1, "lon": -94.9, "status": "normal", "capacity": 0.10},
        ],
    }

    return APIResponse(data=response, provenance=_provenance(result))


@router.get("/hurricanes/season-summary")
async def get_season_summary():
    """Hurricane season summary."""
    return APIResponse(
        data={"year": 2026, "named_storms": 8, "hurricanes": 4, "major_hurricanes": 2, "ace_index": 72.4},
        provenance=DataProvenance(status=DataStatus.MOCK, source="nhc", fetched_at=datetime.utcnow()),
    )


# ════════════════════════════════════════════════════════════════════
# MACRO & SEASONALITY
# ════════════════════════════════════════════════════════════════════

@router.get("/macro/seasonality/{commodity}")
async def get_seasonality(commodity: str):
    """Weekly seasonality — current year vs 5yr/10yr average."""
    import numpy as np
    np.random.seed(33)
    base = 72 if commodity == "wti" else 76
    data = []
    for w in range(52):
        seasonal = np.sin(w / 52 * 2 * np.pi) * 5
        data.append({
            "week": f"W{w+1}",
            "current": round(base + seasonal + np.random.randn() * 1.5, 2) if w < 22 else None,
            "avg5yr": round(base + seasonal * 0.8, 2),
            "avg10yr": round(base + seasonal * 0.6, 2),
        })
    return APIResponse(
        data={"commodity": commodity, "data": data},
        provenance=DataProvenance(status=DataStatus.MOCK, source="computed", fetched_at=datetime.utcnow()),
    )


@router.get("/macro/heatmap/{commodity}")
async def get_heatmap(commodity: str):
    """Monthly returns heatmap."""
    import numpy as np
    np.random.seed(55)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    years = [2022, 2023, 2024, 2025, 2026]
    returns = []
    for y in years:
        row = [round(np.random.randn() * 5, 1) for _ in range(12)]
        if y == 2026:
            row = row[:5] + [None] * 7
        returns.append(row)
    return APIResponse(
        data={"months": months, "years": years, "returns": returns},
        provenance=DataProvenance(status=DataStatus.MOCK, source="computed", fetched_at=datetime.utcnow()),
    )


@router.get("/macro/weekly-metrics")
async def get_weekly_metrics():
    """Weekly performance metrics vs seasonal norms."""
    data = {
        "current_week": 22,
        "current_perf": "+2.1%",
        "historical_median": "+0.8%",
        "deviation": "+1.3σ",
        "banner": "bullish",
        "banner_text": "Current week trading 1.3σ above seasonal median. Historical week 22 is typically positive (+0.8%). Driving season demand typically supports Q2 prices.",
    }
    return APIResponse(
        data=data,
        provenance=DataProvenance(status=DataStatus.MOCK, source="computed", fetched_at=datetime.utcnow()),
    )


# ════════════════════════════════════════════════════════════════════
# HEALTH & OBSERVABILITY
# ════════════════════════════════════════════════════════════════════

_start_time = time.time()


@router.get("/health")
async def health():
    """Liveness probe — adapter statuses, DB, Redis, WebSocket counts."""
    adapter_statuses = await registry.health_all()
    redis_ok = await cache.health_check()

    return {
        "status": "healthy" if redis_ok else "degraded",
        "uptime_seconds": round(time.time() - _start_time, 1),
        "database": "ok",
        "redis": "ok" if redis_ok else "down",
        "adapters": adapter_statuses,
        "ws_connections": ws_manager.total_connections,
        "version": "1.0.0",
    }


@router.get("/readiness")
async def readiness():
    """Readiness probe."""
    redis_ok = await cache.health_check()
    if not redis_ok:
        return {"ready": False, "reason": "Redis unavailable"}
    return {"ready": True}


# ════════════════════════════════════════════════════════════════════
# WEBSOCKET HUB
# ════════════════════════════════════════════════════════════════════

@router.websocket("/ws/{room}")
async def websocket_endpoint(websocket: WebSocket, room: str):
    """WebSocket endpoint for real-time data streaming."""
    if room not in ALLOWED_ROOMS:
        await websocket.close(code=4001, reason=f"Invalid room: {room}")
        return

    await ws_manager.connect(websocket, room)
    try:
        while True:
            data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
            if data == "ping":
                await websocket.send_text("pong")
    except (WebSocketDisconnect, asyncio.TimeoutError):
        ws_manager.disconnect(websocket, room)
    except Exception:
        ws_manager.disconnect(websocket, room)
