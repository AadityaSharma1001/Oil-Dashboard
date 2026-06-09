"""VWAP and Bollinger Band computation for intraday bars."""

import numpy as np
from typing import Optional


def compute_vwap(bars: list[dict]) -> list[dict]:
    """
    Compute VWAP and Bollinger Bands from OHLCV intraday bars.
    
    Each bar: {time, open, high, low, close, volume}
    Returns enriched bars: {time, price, vwap, upper_band, lower_band, band_width, deviation, volume}
    """
    if not bars:
        return []

    cum_pv = 0.0
    cum_vol = 0
    prices = []
    result = []

    for bar in bars:
        price = (bar["high"] + bar["low"] + bar["close"]) / 3  # Typical price
        volume = bar.get("volume", 0) or 1  # Avoid zero

        cum_pv += price * volume
        cum_vol += volume
        vwap = cum_pv / cum_vol

        prices.append(price)

        # 20-period rolling standard deviation for Bollinger Bands
        window = prices[-20:]
        if len(window) >= 2:
            std = float(np.std(window, ddof=1))
        else:
            std = 0.0

        upper = vwap + 2 * std
        lower = vwap - 2 * std
        band_width = 4 * std
        deviation = (price - vwap) / std if std > 0 else 0.0

        result.append({
            "time": bar["time"],
            "price": round(price, 3),
            "vwap": round(vwap, 3),
            "upper_band": round(upper, 3),
            "lower_band": round(lower, 3),
            "band_width": round(band_width, 3),
            "deviation": round(deviation, 2),
            "volume": volume,
        })

    return result


def compute_vwap_metrics(enriched_bars: list[dict]) -> dict:
    """Extract summary metrics from VWAP-enriched bars."""
    if not enriched_bars:
        return {"last_vwap": 0, "last_band_width": 0, "last_deviation": 0}

    last = enriched_bars[-1]
    return {
        "last_vwap": last["vwap"],
        "last_band_width": last["band_width"],
        "last_deviation": last["deviation"],
    }
