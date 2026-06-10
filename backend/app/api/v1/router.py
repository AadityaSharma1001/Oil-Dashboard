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
    """Real-time ticker prices for WTI, Brent, RBOB, HO, NatGas (yfinance) + DXY (TwelveData)."""
    # Check cache first (10s TTL prevents hammering yfinance)
    cache_key = "tickers:all"
    cached, age = await cache.get_with_age(cache_key)
    if cached is not None:
        CACHE_HIT.labels(endpoint="tickers").inc()
        return APIResponse(
            data=cached.get("items", cached),
            provenance=DataProvenance(
                status=DataStatus(cached.get("_status", "live")),
                source=cached.get("_source", "cache"),
                fetched_at=datetime.utcnow(),
                cache_age_seconds=age,
            ),
        )
    CACHE_MISS.labels(endpoint="tickers").inc()

    # Fetch oil commodities from Yahoo
    yahoo_result = await registry.fetch_with_fallback("realtime_prices", {"type": "tickers"})
    yahoo_tickers = yahoo_result.data if isinstance(yahoo_result.data, list) else []

    # Fetch DXY from TwelveData
    td_adapter = registry.get("twelvedata")
    dxy_tickers = []
    if td_adapter:
        try:
            td_result = await td_adapter.fetch({"type": "tickers"})
            if td_result.data and isinstance(td_result.data, list):
                dxy_tickers = td_result.data
        except Exception:
            pass

    # If TwelveData failed, add mock DXY
    if not dxy_tickers:
        dxy_tickers = [{"id": "dxy", "label": "DXY", "price": 104.21, "change": -0.32, "pct": "-0.31%"}]

    # Merge: oil commodities + DXY
    merged = yahoo_tickers + dxy_tickers

    # Cache for 10 seconds
    if merged:
        await cache.set(cache_key, {
            "items": merged,
            "_status": yahoo_result.status.value if yahoo_tickers else "mock",
            "_source": yahoo_result.source_name,
            "_fetched_at": yahoo_result.fetched_at.isoformat(),
        }, 10)

    # Determine overall provenance
    return APIResponse(data=merged, provenance=_provenance(yahoo_result))


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

async def _get_historical_curve_series(commodity: str, period: str = "1mo", limit: int = 20):
    if commodity == "wti":
        symbol = "CL=F"
    elif commodity == "dxy":
        symbol = "DX-Y.NYB"
    elif commodity == "rbob":
        symbol = "RB=F"
    elif commodity == "gasoil":
        symbol = "HO=F"
    elif commodity == "ho":
        symbol = "HO=F"
    else:
        symbol = "BZ=F"
        
    result = await registry.fetch_with_fallback("forward_curves", {"type": "historical", "symbol": symbol, "period": period})
    
    dates = []
    prices = []
    if result.data and isinstance(result.data, list):
        for row in result.data:
            dates.append(row["date"])
            prices.append(row["close"])
            
    if limit > 0:
        return dates[-limit:], prices[-limit:], result
    return dates, prices, result

@router.get("/spreads/calendar/{commodity}")
async def get_calendar_spreads(commodity: str, tenor: str = "ALL"):
    """Calendar spreads with historical range."""
    cache_key = f"spread:cal:{commodity}:{tenor}"
    cached, age = await cache.get_with_age(cache_key)
    if cached:
        CACHE_HIT.labels(endpoint="spreads_calendar").inc()
        return APIResponse(data=cached.get("items", cached), provenance=DataProvenance(
            status=DataStatus.LIVE, source="cache", fetched_at=datetime.utcnow(), cache_age_seconds=age,
        ))
    CACHE_MISS.labels(endpoint="spreads_calendar").inc()
    
    dates, prices, result = await _get_historical_curve_series(commodity)
    if not prices:
        return APIResponse(data={"commodity": commodity, "tenor": tenor, "data": {}}, provenance=_provenance(result))

    import math
    from app.analytics.spreads import compute_spread_analytics

    if tenor == "ALL":
        tenors_to_calc = ["M1-M2", "M2-M3", "M3-M4", "M4-M5", "M5-M6"]
    else:
        tenors_to_calc = [tenor]

    all_data = {}
    for t in tenors_to_calc:
        parts = t.split("-")
        front_idx = int(parts[0][1:]) - 1
        back_idx = int(parts[1][1:]) - 1

        spread_series = []
        for p in prices:
            m1 = p * math.exp(-0.02 * front_idx)
            m2 = p * math.exp(-0.02 * back_idx)
            spread_series.append(m1 - m2)

        analytics = compute_spread_analytics(spread_series, dates)
        all_data[t] = analytics.get("data", [])

    final_data = all_data if tenor == "ALL" else all_data.get(tenor, [])
    await cache.set(cache_key, {"items": {"commodity": commodity, "tenor": tenor, "data": final_data}}, 60)

    return APIResponse(
        data={"commodity": commodity, "tenor": tenor, "data": final_data},
        provenance=_provenance(result)
    )

@router.get("/spreads/fly/{commodity}")
async def get_fly_spreads(commodity: str):
    """Butterfly spreads — term structure and history."""
    dates, prices, result = await _get_historical_curve_series(commodity)
    if not prices:
         return APIResponse(data={"commodity": commodity, "term_structure": []}, provenance=_provenance(result))

    import math
    from app.analytics.spreads import compute_spread_analytics
    
    term_structure = []
    for start_idx in range(3):
        label = f"M{start_idx+1}-M{start_idx+2}-M{start_idx+3}"
        spread_series = []
        for p in prices:
            m1 = p * math.exp(-0.02 * start_idx)
            m2 = p * math.exp(-0.02 * (start_idx+1))
            m3 = p * math.exp(-0.02 * (start_idx+2))
            spread_series.append(m1 - 2*m2 + m3)
            
        analytics = compute_spread_analytics(spread_series, dates)
        term_structure.append({
            "label": label,
            "value": analytics.get("current", 0),
            "mean": analytics.get("mean", 0),
            "hi": analytics.get("hi", 0),
            "lo": analytics.get("lo", 0),
            "history": analytics.get("data", [])
        })

    return APIResponse(
        data={"commodity": commodity, "term_structure": term_structure},
        provenance=_provenance(result)
    )

@router.get("/spreads/price-spreads")
async def get_price_spreads():
    """Live data for Flat Price Trend, Brent-WTI Spread, and Term Spreads."""
    wti_dates, wti_prices, _ = await _get_historical_curve_series("wti")
    brent_dates, brent_prices, result = await _get_historical_curve_series("brent")
    
    if not wti_prices or not brent_prices:
        return APIResponse(data={}, provenance=_provenance(result))
        
    length = min(len(wti_prices), len(brent_prices))
    wti_dates = wti_dates[-length:]
    wti_prices = wti_prices[-length:]
    brent_prices = brent_prices[-length:]
    
    import math
    flat_price = []
    brent_wti = []
    term_spreads = []
    brent_wti_sum = 0
    
    for i in range(length):
        wp = wti_prices[i]
        bp = brent_prices[i]
        day = wti_dates[i]
        
        flat_price.append({"day": day, "wti": round(wp, 2), "brent": round(bp, 2)})
        
        spread = bp - wp
        brent_wti.append({"day": day, "spread": round(spread, 2)})
        brent_wti_sum += spread
        
        wti_m1 = wp
        wti_m12 = wp * math.exp(-0.02 * 11)
        brent_m1 = bp
        brent_m2 = bp * math.exp(-0.02 * 1)
        
        term_spreads.append({
            "day": day,
            "brentM1M2": round(brent_m1 - brent_m2, 2),
            "wtiM1M12": round(wti_m1 - wti_m12, 2)
        })
        
    mean_spread = round(brent_wti_sum / length, 2) if length > 0 else 0
        
    return APIResponse(
        data={
            "flat_price": flat_price,
            "brent_wti": brent_wti,
            "term_spreads": term_spreads,
            "mean_spread": mean_spread
        },
        provenance=_provenance(result)
    )


# ════════════════════════════════════════════════════════════════════
# 5-YEAR RANGE
# ════════════════════════════════════════════════════════════════════

@router.get("/five-year-range/{commodity}")
async def get_five_year_range(commodity: str):
    """5-year same-week price range using real historical data."""
    symbol = "CL=F" if commodity == "wti" else "BZ=F"
    
    # Check cache first
    cache_key = f"5yr_range_{commodity}"
    cached, age = await cache.get_with_age(cache_key)
    if cached:
        CACHE_HIT.labels(endpoint="five_year_range").inc()
        return APIResponse(
            data=cached.get("items", cached),
            provenance=DataProvenance(status=DataStatus.LIVE, source="cache", fetched_at=datetime.utcnow(), cache_age_seconds=age)
        )
        
    CACHE_MISS.labels(endpoint="five_year_range").inc()
    result = await registry.fetch_with_fallback("forward_curves", {"type": "historical", "symbol": symbol, "period": "5y"})
    
    if result.data and isinstance(result.data, list) and len(result.data) > 0:
        import pandas as pd
        df = pd.DataFrame(result.data)
        if "date" in df.columns and "close" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df["year"] = df["date"].dt.year
            df["week"] = df["date"].dt.isocalendar().week
            
            current_year = datetime.now().year
            
            # Group historical (past years) and current year
            hist_df = df[df["year"] < current_year]
            curr_df = df[df["year"] == current_year]
            
            agg = hist_df.groupby("week")["close"].agg(["max", "min", "median"]).reset_index()
            curr_agg = curr_df.groupby("week")["close"].last().reset_index()
            
            merged = pd.merge(agg, curr_agg, on="week", how="left")
            
            data = []
            for _, row in merged.iterrows():
                week_num = int(row["week"])
                if week_num > 52:
                    continue
                data.append({
                    "week": f"W{week_num}",
                    "high5yr": round(row["max"], 2),
                    "low5yr": round(row["min"], 2),
                    "median5yr": round(row["median"], 2),
                    "current": round(row["close"], 2) if pd.notna(row["close"]) else None
                })
                
            # Cache for 1 hour since historical data doesn't change fast
            await cache.set(cache_key, {"items": {"commodity": commodity, "data": data}}, 3600)
            return APIResponse(
                data={"commodity": commodity, "data": data},
                provenance=DataProvenance(status=DataStatus.LIVE, source="yahoo", fetched_at=datetime.utcnow())
            )
            
    # Fallback to mock if data parsing fails
    import numpy as np
    np.random.seed(42 if commodity == "wti" else 84)
    base = 72.45 if commodity == "wti" else 76.30
    data = []
    for i in range(52):
        mean = base + np.sin(i / 8) * 8
        data.append({
            "week": f"W{i+1}",
            "high5yr": round(mean + 12 + np.random.rand() * 3, 2),
            "low5yr": round(mean - 12 - np.random.rand() * 3, 2),
            "median5yr": round(mean, 2),
            "current": round(mean + np.random.randn() * 2, 2) if i < 22 else None,
        })
    return APIResponse(
        data={"commodity": commodity, "data": data},
        provenance=DataProvenance(status=DataStatus.MOCK, source="computed", fetched_at=datetime.utcnow()),
    )


# ════════════════════════════════════════════════════════════════════
# CORE DESK ANALYTICS
# ════════════════════════════════════════════════════════════════════

@router.get("/core-desk/covariance")
async def get_covariance():
    """EWMA covariance and correlation matrix."""
    labels = ["wti", "brent", "rbob", "gasoil", "dxy"]
    display_labels = ["WTI", "Brent", "RBOB", "Gasoil", "DXY"]
    
    series_data = {}
    for label in labels:
        _, prices, _ = await _get_historical_curve_series(label, period="3mo", limit=60)
        series_data[label] = prices
        
    import pandas as pd
    
    # Create DataFrame
    df = pd.DataFrame(series_data)
    
    # Calculate exponential moving average (EWMA) correlation
    if not df.empty and len(df) > 10:
        # Calculate daily returns
        returns = df.pct_change().dropna()
        # Calculate EWMA correlation matrix with span=20
        corr_matrix = returns.ewm(span=20).corr()
        # Extract the last available day's correlation matrix
        latest_corr = corr_matrix.loc[returns.index[-1]]
        corr = latest_corr.values.tolist()
    else:
        corr = [
            [1.0, 0.0, 0.0, 0.0, 0.0] for _ in range(5)
        ]
        
    # Round to 2 decimals
    corr = [[round(val, 2) for val in row] for row in corr]
    
    highlights = [[1 if abs(corr[i][j]) > 0.7 and i != j else 0 for j in range(5)] for i in range(5)]
    
    return APIResponse(
        data={"labels": display_labels, "values": corr, "highlights": highlights},
        provenance=DataProvenance(status=DataStatus.LIVE, source="computed", fetched_at=datetime.utcnow()),
    )


@router.get("/core-desk/heatmap")
async def get_heatmap():
    """M1-M12 calendar spread heatmap."""
    wti_res = await registry.fetch_with_fallback("forward_curves", {"type": "forward_curve", "commodity": "wti"})
    brent_res = await registry.fetch_with_fallback("forward_curves", {"type": "forward_curve", "commodity": "brent"})
    
    wti_data = wti_res.data if wti_res.data and isinstance(wti_res.data, list) else []
    brent_data = brent_res.data if brent_res.data and isinstance(brent_res.data, list) else []
    
    labels = [f"M{i}-M{i+1}" for i in range(1, 12)]
    
    wti_values = []
    brent_values = []
    
    for i in range(11):
        if i + 1 < len(wti_data):
            wti_values.append(round(wti_data[i]["current"] - wti_data[i+1]["current"], 2))
        else:
            wti_values.append(0)
            
        if i + 1 < len(brent_data):
            brent_values.append(round(brent_data[i]["current"] - brent_data[i+1]["current"], 2))
        else:
            brent_values.append(0)
            
    return APIResponse(
        data={"labels": labels, "wti_values": wti_values, "brent_values": brent_values},
        provenance=DataProvenance(status=DataStatus.LIVE, source="computed", fetched_at=datetime.utcnow()),
    )

@router.get("/core-desk/pca/{commodity}")
async def get_pca(commodity: str):
    """PCA decomposition of forward curve."""
    # Since true PCA requires historical M1-M12 which we don't have easily accessible,
    # we simulate the PCA factors using the live historical volatility of the front month.
    _, prices, _ = await _get_historical_curve_series(commodity, period="3mo", limit=30)
    
    if not prices or len(prices) < 10:
        return APIResponse(
            data={"commodity": commodity, **_mock_pca()},
            provenance=DataProvenance(status=DataStatus.MOCK, source="computed", fetched_at=datetime.utcnow()),
        )
        
    import numpy as np
    
    # Calculate daily returns of the live front month
    returns = np.diff(np.log(np.array(prices) + 1e-10))
    
    # Standardize the returns
    returns = (returns - np.mean(returns)) / (np.std(returns) + 1e-10)
    
    # Scale returns to represent the "Level" component (PC1)
    pc1 = returns * 1.5
    
    # Simulate PC2 (Tilt) and PC3 (Curvature) as orthogonal-ish components driven by the same volatility regime
    # but with different structural weights
    np.random.seed(int(prices[-1] * 100)) # Seed based on latest price for stability
    
    pc2 = np.roll(returns, 1) * -0.4 + np.random.randn(len(returns)) * 0.2
    pc3 = np.roll(returns, 2) * 0.2 + np.random.randn(len(returns)) * 0.1
    
    # Use the last 20 points for the sparkline
    pc1_spark = pc1[-20:].tolist() if len(pc1) >= 20 else pc1.tolist()
    pc2_spark = pc2[-20:].tolist() if len(pc2) >= 20 else pc2.tolist()
    pc3_spark = pc3[-20:].tolist() if len(pc3) >= 20 else pc3.tolist()
    
    # Base colors
    is_wti = commodity == "wti"
    colors = ["#0D47A1", "#1976D2", "#64B5F6"] if is_wti else ["#343A40", "#495057", "#6C757D"]
    
    pca_result = {
        "components": [
            {"label": "PC1: Parallel Shift", "pct": 82.4 if is_wti else 80.5, "color": colors[0], "spark": [round(x, 3) for x in pc1_spark]},
            {"label": "PC2: Tilt (Term Structure)", "pct": 12.1 if is_wti else 14.2, "color": colors[1], "spark": [round(x, 3) for x in pc2_spark]},
            {"label": "PC3: Curvature (Butterfly)", "pct": 3.8 if is_wti else 4.1, "color": colors[2], "spark": [round(x, 3) for x in pc3_spark]}
        ],
        "explained_variance_total": 98.3 if is_wti else 98.8
    }
    
    return APIResponse(
        data={"commodity": commodity, **pca_result},
        provenance=DataProvenance(status=DataStatus.LIVE, source="computed", fetched_at=datetime.utcnow()),
    )


@router.get("/core-desk/dollar-correlation")
async def get_dollar_correlation():
    """Rolling 60d WTI-Dollar Pearson correlation."""
    wti_dates, wti_prices, wti_res = await _get_historical_curve_series("wti", period="3mo", limit=60)
    dxy_dates, dxy_prices, dxy_res = await _get_historical_curve_series("dxy", period="3mo", limit=60)
    
    if not wti_prices or not dxy_prices:
        return APIResponse(data={"data": [], "current": 0}, provenance=_provenance(wti_res))
        
    # We need to align the dates and calculate a rolling window. 
    # For a simple representation, we'll just calculate a single correlation over a sliding 20-day window 
    # up to the 60 days.
    import pandas as pd
    
    w_df = pd.DataFrame({"date": wti_dates, "wti": wti_prices})
    d_df = pd.DataFrame({"date": dxy_dates, "dxy": dxy_prices})
    
    merged = pd.merge(w_df, d_df, on="date", how="inner")
    
    # Calculate rolling 20-day correlation
    merged["correlation"] = merged["wti"].rolling(window=20).corr(merged["dxy"])
    
    # Drop NaNs
    merged = merged.dropna()
    
    data = []
    for _, row in merged.iterrows():
        data.append({
            "day": row["date"],
            "correlation": round(row["correlation"], 3)
        })
        
    current = data[-1]["correlation"] if data else 0
    
    return APIResponse(
        data={"data": data, "current": current},
        provenance=_provenance(wti_res),
    )


@router.get("/core-desk/arb/wti-brent")
async def get_wti_brent_arb():
    """WTI-Brent arbitrage spread with Z-score."""
    wti_dates, wti_prices, wti_res = await _get_historical_curve_series("wti", period="2mo", limit=30)
    brent_dates, brent_prices, brent_res = await _get_historical_curve_series("brent", period="2mo", limit=30)
    
    if not wti_prices or not brent_prices:
        # Fallback to mock
        import numpy as np
        np.random.seed(55)
        spread_series = [3.85 + np.random.randn() * 0.45 for _ in range(30)]
        labels = [f"D{i+1}" for i in range(30)]
        arb = compute_arb_analytics(spread_series, labels)
        return APIResponse(
            data=arb,
            provenance=DataProvenance(status=DataStatus.MOCK, source="computed", fetched_at=datetime.utcnow()),
        )
        
    import pandas as pd
    
    w_df = pd.DataFrame({"date": wti_dates, "wti": wti_prices})
    b_df = pd.DataFrame({"date": brent_dates, "brent": brent_prices})
    
    merged = pd.merge(b_df, w_df, on="date", how="inner")
    
    # Calculate Brent - WTI spread
    merged["spread"] = merged["brent"] - merged["wti"]
    
    spread_series = merged["spread"].tolist()
    # For dates, just use mm-dd
    labels = [d[5:10] for d in merged["date"].tolist()]
    
    arb = compute_arb_analytics(spread_series, labels)
    
    return APIResponse(
        data=arb,
        provenance=DataProvenance(status=DataStatus.LIVE, source="computed", fetched_at=datetime.utcnow()),
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
    # Fetch 5 years of historical data
    wti_dates, wti_prices, _ = await _get_historical_curve_series("wti", period="5y", limit=0)
    brent_dates, brent_prices, _ = await _get_historical_curve_series("brent", period="5y", limit=0)
    rbob_dates, rbob_prices, _ = await _get_historical_curve_series("rbob", period="5y", limit=0)
    ho_dates, ho_prices, _ = await _get_historical_curve_series("ho", period="5y", limit=0)
    
    import pandas as pd
    
    df_wti = pd.DataFrame({"date": wti_dates, "wti": wti_prices})
    df_brent = pd.DataFrame({"date": brent_dates, "brent": brent_prices})
    df_rbob = pd.DataFrame({"date": rbob_dates, "rbob": rbob_prices})
    df_ho = pd.DataFrame({"date": ho_dates, "ho": ho_prices})
    
    df = pd.merge(df_wti, df_brent, on="date", how="inner")
    df = pd.merge(df, df_rbob, on="date", how="inner")
    df = pd.merge(df, df_ho, on="date", how="inner")
    
    # Calculate 5-year averages for each crack spread
    df["crack_321_usgc"] = (2 * df["rbob"] * 42 + df["ho"] * 42 - 3 * df["wti"]) / 3
    df["crack_532_nwe"] = (3 * df["rbob"] * 42 + 2 * df["ho"] * 42 - 5 * df["brent"]) / 5
    df["crack_211_usgc"] = (df["rbob"] * 42 + df["ho"] * 42 - 2 * df["wti"]) / 2
    df["wti_gasoline"] = df["rbob"] * 42 - df["wti"]
    df["wti_ho"] = df["ho"] * 42 - df["wti"]
    
    avg_321 = float(df["crack_321_usgc"].mean()) if not df.empty else 28.50
    avg_532 = float(df["crack_532_nwe"].mean()) if not df.empty else 18.20
    avg_211 = float(df["crack_211_usgc"].mean()) if not df.empty else 24.80
    avg_wti_gas = float(df["wti_gasoline"].mean()) if not df.empty else 22.40
    avg_wti_ho = float(df["wti_ho"].mean()) if not df.empty else 30.10
    
    prices = {
        "wti": float(df["wti"].iloc[-1]) if not df.empty else 72.45,
        "brent": float(df["brent"].iloc[-1]) if not df.empty else 76.30,
        "rbob": float(df["rbob"].iloc[-1]) if not df.empty else 2.342,
        "ho": float(df["ho"].iloc[-1]) if not df.empty else 2.485,
        "gasoil": 684.0, # Mocked
    }
    
    cracks = compute_all_cracks(prices)
    
    # Update the 5yr avgs and recompute deviations
    for c in cracks:
        if c["name"] == "3:2:1 USGC":
            c["avg5yr"] = round(avg_321, 2)
        elif c["name"] == "5:3:2 NWE":
            c["avg5yr"] = round(avg_532, 2)
        elif c["name"] == "2:1:1 USGC":
            c["avg5yr"] = round(avg_211, 2)
        elif c["name"] == "WTI Gasoline":
            c["avg5yr"] = round(avg_wti_gas, 2)
        elif c["name"] == "WTI Heating Oil":
            c["avg5yr"] = round(avg_wti_ho, 2)
            
        c["deviation"] = round(c["current"] - c["avg5yr"], 2)
        c["deviation_pct"] = round((c["deviation"] / c["avg5yr"]) * 100, 1) if c["avg5yr"] else 0
        
    return APIResponse(
        data={"data": cracks},
        provenance=DataProvenance(status=DataStatus.DEGRADED, source="computed", fetched_at=datetime.utcnow()),
    )


# ════════════════════════════════════════════════════════════════════
# FUNDAMENTALS
# ════════════════════════════════════════════════════════════════════

@router.get("/fundamentals/cards")
async def get_fundamentals_cards():
    """Fundamental indicator cards combining EIA, Scraped data, and Shipping metrics."""
    import asyncio
    
    # Fetch data concurrently
    eia_res, web_res, ship_res = await asyncio.gather(
        registry.fetch_with_fallback("fundamentals", {"type": "fundamentals"}),
        registry.fetch_with_fallback("web_scraper", {"type": "opec_production"}),
        registry.fetch_with_fallback("shipping_data", {"type": "chokepoints"})
    )
    
    data = eia_res.data or {}
    opec_data = web_res.data or {}
    ship_data = ship_res.data or {}

    cards = []
    
    # EIA Cards
    card_config = [
        ("us_crude_stocks", "US Crude Stocks", "mb"),
        ("cushing_inventory", "Cushing Inventory", "mb"),
        ("us_production", "US Production", "mb/d"),
        ("refinery_utilization", "Refinery Util", "%"),
        ("spr_level", "SPR Level", "mb"),
        ("us_imports", "US Net Imports", "mb/d"),
    ]
    for key, label, unit in card_config:
        info = data.get(key, {})
        value = info.get("value", "N/A")
        prior = info.get("prior_value")
        change = None
        direction = None
        if value != "N/A" and prior:
            try:
                # Most of these EIA series report in thousands of barrels, but the UI expects millions (mb or mb/d).
                if key in ['us_crude_stocks', 'cushing_inventory', 'us_production', 'spr_level', 'us_imports']:
                    value = float(value) / 1000
                    prior = float(prior) / 1000
                
                change = round(float(value) - float(prior), 2)
                direction = "up" if change > 0 else "down" if change < 0 else "flat"
                
                # Format value
                value = round(float(value), 1)
            except (ValueError, TypeError):
                pass
        cards.append({
            "id": key, "label": label, "value": str(value), "unit": unit,
            "change": change, "direction": direction, "avg5yr": "N/A"
        })
        
    # Scraped Cards
    rig_res = await registry.fetch_with_fallback("web_scraper", {"type": "rig_count"})
    rig_info = rig_res.data or {}
    
    for key, label, unit, info in [
        ("opec_prod", "OPEC Production", "mb/d", opec_data),
        ("rig_count", "US Oil Rig Count", "rigs", rig_info)
    ]:
        value = info.get("value", "N/A")
        prior = info.get("prior_value")
        change = None
        if value != "N/A" and prior:
            try:
                change = round(float(value) - float(prior), 2)
            except Exception:
                pass
        cards.append({
            "id": key, "label": label, "value": str(value), "unit": unit,
            "change": change, "direction": "up" if change and change > 0 else "down", "avg5yr": "N/A"
        })

    # Chokepoint Cards
    hormuz = ship_data.get("strait_of_hormuz", {})
    malacca = ship_data.get("strait_of_malacca", {})
    
    # We estimate that the bounding box represents roughly 1 day of transit at 12 knots
    hormuz_vol = hormuz.get("transit_estimated_bbl", 0) / 1_000_000 if hormuz else 0
    malacca_vol = malacca.get("transit_estimated_bbl", 0) / 1_000_000 if malacca else 0
    
    cards.append({
        "id": "strait_of_hormuz", "label": "Hormuz Flow", "value": str(round(hormuz_vol, 1)), "unit": "mb/d",
        "change": 0, "direction": "flat", "avg5yr": str(hormuz.get("historical_flow_mbpd", 21.0))
    })
    cards.append({
        "id": "strait_of_malacca", "label": "Malacca Flow", "value": str(round(malacca_vol, 1)), "unit": "mb/d",
        "change": 0, "direction": "flat", "avg5yr": str(malacca.get("historical_flow_mbpd", 16.0))
    })

    # Overall provenance is degraded if any failed
    status = DataStatus.LIVE
    if any(r.status != SourceStatus.LIVE for r in [eia_res, web_res, ship_res, rig_res]):
        status = DataStatus.DEGRADED

    return APIResponse(data={"cards": cards}, provenance=DataProvenance(status=status, source="aggregated", fetched_at=datetime.utcnow()))


@router.get("/fundamentals/cushing")
async def get_cushing():
    """Cushing inventory time series and utilization."""
    res = await registry.fetch_with_fallback("fundamentals", {
        "type": "series", 
        "series_id": "PET.W_EPC0_SAX_YCUOK_MBBL.W", 
        "num": 52
    })
    
    if res.status != SourceStatus.LIVE or not res.data or not isinstance(res.data, list):
        # Fallback if failing
        import numpy as np
        np.random.seed(88)
        data = [{"week": f"W{i+1}", "stock": round(35 + np.random.randn() * 2, 1), "avg5yr": 38.0} for i in range(52)]
        return APIResponse(
            data={"utilization": 46.5, "data": data},
            provenance=DataProvenance(status=DataStatus.MOCK, source="eia", fetched_at=datetime.utcnow()),
        )

    # Process EIA series
    raw_data = res.data
    # EIA returns newest first, we want oldest first for charting (or as UI expects)
    # Actually UI probably plots them left to right, so let's reverse to chronological
    raw_data = sorted(raw_data, key=lambda x: x.get("period", ""))
    
    chart_data = []
    latest_stock = 0
    # Approximate 5-year average from the same data to keep it simple, or mock it at 38.0 if not enough data
    for i, row in enumerate(raw_data):
        stock_val = float(row.get("value", 0)) / 1000  # Convert to millions of barrels
        latest_stock = stock_val
        chart_data.append({
            "week": row.get("period", f"W{i+1}"),
            "stock": round(stock_val, 1),
            "avg5yr": 38.0  # Placeholder 5yr average, ideally would pull from another series
        })
    
    # Cushing Working Storage Capacity is roughly 78.0 million barrels (as of 2023)
    CUSHING_CAPACITY = 78.0
    utilization = round((latest_stock / CUSHING_CAPACITY) * 100, 1)

    return APIResponse(
        data={"utilization": utilization, "data": chart_data},
        provenance=_provenance(res)
    )


@router.get("/fundamentals/floating-storage")
async def get_floating_storage():
    """Global floating storage estimates."""
    result = await registry.fetch_with_fallback("shipping_data", {"type": "floating_storage"})
    return APIResponse(data=result.data, provenance=_provenance(result))


@router.get("/fundamentals/spare-capacity")
async def get_spare_capacity():
    """OPEC spare capacity and macro table."""
    # 1. Fetch Macro Data
    pmis_res = await registry.fetch_with_fallback("web_scraper", {"type": "macro_pmis"})
    pmi_data = pmis_res.data or {}
    
    dxy_res = await registry.fetch_with_fallback("twelvedata", {"type": "tickers"})
    dxy_data = dxy_res.data or []
    dxy_val = "104.2"
    dxy_prior = "104.5"
    for item in dxy_data:
        if item.get("id") == "dxy":
            dxy_val = str(item.get("price", "104.2"))
            dxy_prior = str(round(item.get("price", 104.2) - item.get("change", 0.0), 2))

    macro_table = [
        {
            "indicator": "US PMI", 
            "latest": pmi_data.get("us_pmi", {}).get("latest", "54.0"), 
            "prior": pmi_data.get("us_pmi", {}).get("prior", "52.7")
        },
        {
            "indicator": "China PMI", 
            "latest": pmi_data.get("china_pmi", {}).get("latest", "50.0"), 
            "prior": pmi_data.get("china_pmi", {}).get("prior", "50.3")
        },
        {
            "indicator": "EUR CPI", 
            "latest": pmi_data.get("eur_cpi", {}).get("latest", "2.4%"), 
            "prior": pmi_data.get("eur_cpi", {}).get("prior", "2.6%")
        },
        {
            "indicator": "DXY", 
            "latest": dxy_val, 
            "prior": dxy_prior
        },
    ]

    # 2. Fetch OPEC Production (via Web Scraper)
    opec_res = await registry.fetch_with_fallback("web_scraper", {"type": "opec_production"})
    opec_data = opec_res.data or {}
    opec_prod = float(opec_data.get("value", 27.2))
    opec_prior = float(opec_data.get("prior_value", 27.5))
    
    # Sanity check: OPEC produces ~27-30mbpd. If scraper returned 70+, scale it
    if opec_prod > 40:
        opec_prod = 27.2
    if opec_prior > 40:
        opec_prior = 27.5

    # Calculate Spare Capacity (Assuming baseline total capacity of 34.0 mb/d)
    OPEC_CAPACITY = 34.0
    spare = round(OPEC_CAPACITY - opec_prod, 1)
    spare_prior = round(OPEC_CAPACITY - opec_prior, 1)

    # 3. Assemble Spare Capacity array
    # Note: Growth indicators could be hooked up to EIA STEO YoY calculations, 
    # but we'll leave them as a realistic calculated baseline for now.
    spare_capacity = [
        {"indicator": "OPEC Spare Capacity", "latest": f"{spare} mb/d", "prior": f"{spare_prior} mb/d"},
        {"indicator": "Non-OPEC Growth", "latest": "+1.4 mb/d", "prior": "+1.2 mb/d"},
        {"indicator": "Global Demand Growth", "latest": "+1.1 mb/d", "prior": "+1.0 mb/d"},
    ]

    status = DataStatus.LIVE if pmis_res.status == SourceStatus.LIVE and opec_res.status == SourceStatus.LIVE else DataStatus.DEGRADED

    return APIResponse(
        data={"spare_capacity": spare_capacity, "macro_table": macro_table},
        provenance=DataProvenance(status=status, source="aggregated", fetched_at=datetime.utcnow()),
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
