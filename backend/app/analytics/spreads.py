"""Spread calculations — calendar, butterfly, arbitrage."""

import numpy as np
from typing import Optional
from app.analytics.statistics import z_score


def calendar_spread(
    front_prices: list[float], back_prices: list[float]
) -> list[float]:
    """Calendar spread = front - back contract."""
    return [f - b for f, b in zip(front_prices, back_prices)]


def butterfly_spread(
    front: list[float], middle: list[float], back: list[float]
) -> list[float]:
    """Butterfly spread = front - 2*middle + back."""
    return [f - 2 * m + b for f, m, b in zip(front, middle, back)]


def compute_spread_analytics(
    spread_series: list[float], labels: list[str]
) -> dict:
    """
    Compute spread analytics: mean, std, hi, lo, current, z-score.
    """
    if not spread_series:
        return {}

    current = spread_series[-1]
    mean = float(np.mean(spread_series))
    std = float(np.std(spread_series, ddof=1)) if len(spread_series) > 1 else 0.0
    hi = float(np.max(spread_series))
    lo = float(np.min(spread_series))
    z = z_score(current, mean, std)

    data = [
        {"day": labels[i], "value": round(spread_series[i], 3), "mean": round(mean, 3), "hi": round(hi, 3), "lo": round(lo, 3)}
        for i in range(len(spread_series))
    ]

    return {
        "data": data,
        "current": round(current, 3),
        "mean": round(mean, 3),
        "std": round(std, 3),
        "z_score": round(z, 2),
        "hi": round(hi, 3),
        "lo": round(lo, 3),
    }


def compute_arb_analytics(
    spread_series: list[float], labels: list[str], window: int = 30
) -> dict:
    """Compute spread arbitrage analytics with Z-score bands."""
    if len(spread_series) < window:
        window = max(len(spread_series), 2)

    recent = spread_series[-window:]
    mean_30d = float(np.mean(recent))
    std_30d = float(np.std(recent, ddof=1)) if len(recent) > 1 else 0.0
    current = spread_series[-1]
    z = z_score(current, mean_30d, std_30d)

    data = []
    for i in range(len(spread_series)):
        data.append({
            "day": labels[i],
            "spread": round(spread_series[i], 3),
            "mean": round(mean_30d, 3),
            "upper": round(mean_30d + std_30d, 3),
            "lower": round(mean_30d - std_30d, 3),
        })

    return {
        "data": data,
        "current_spread": round(current, 3),
        "mean_30d": round(mean_30d, 3),
        "std_30d": round(std_30d, 3),
        "z_score": round(z, 2),
    }


def m1_m12_heatmap(futures_prices: list[list[float]], tenors: int = 12) -> list[list[float]]:
    """
    Compute M1-M12 inter-month spread heatmap.
    Input: daily snapshots of 12 monthly futures. Shape: [T, 12]
    Output: heatmap of average spreads [12, 12]
    """
    data = np.array(futures_prices)
    if data.shape[1] < tenors:
        return []

    latest = data[-1, :tenors]
    spreads = []
    for i in range(tenors):
        row = []
        for j in range(tenors):
            row.append(round(float(latest[i] - latest[j]), 3))
        spreads.append(row)
    return spreads
