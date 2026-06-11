"""VWAP and Bollinger Band computation for intraday bars."""

import numpy as np
from typing import Optional


def compute_vwap(bars: list[dict], daily_closes: list[float] = None) -> list[dict]:
    """
    Compute VWAP and Bollinger Bands from OHLCV intraday bars.
    
    If daily_closes is provided, the Bollinger Bands are calculated as a 20-day rolling
    band using the previous daily closes plus the current intraday price. Otherwise,
    it falls back to a 20-period rolling band on the intraday data.
    
    Each bar: {time, open, high, low, close, volume}
    Returns enriched bars: {time, price, vwap, upper_band, lower_band, band_width, deviation, volume}
    """
    if not bars:
        return []

    cum_pv = 0.0
    cum_vol = 0
    cum_pv2 = 0.0  # For variance
    result = []
    
    for bar in bars:
        price = (bar["high"] + bar["low"] + bar["close"]) / 3  # Typical price
        volume = bar.get("volume", 0) or 1  # Avoid zero

        cum_pv += price * volume
        cum_vol += volume
        cum_pv2 += volume * (price ** 2)

        vwap = cum_pv / cum_vol

        variance = max(0, (cum_pv2 / cum_vol) - (vwap ** 2))
        std_vwap = np.sqrt(variance)

        if std_vwap > 0:
            z_score = float((price - vwap) / std_vwap)
        else:
            z_score = 0.0

        result.append({
            "time": bar["time"],
            "price": round(price, 3),
            "z_score": round(z_score, 3),
            "volume": volume,
        })

    return result


def compute_vwap_metrics(enriched_bars: list[dict]) -> dict:
    """Extract summary metrics from VWAP-enriched bars."""
    if not enriched_bars:
        return {"last_z_score": 0, "last_price": 0}

    last = enriched_bars[-1]
    return {
        "last_z_score": last["z_score"],
        "last_price": last["price"],
    }
