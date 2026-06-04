"""Core statistical computations used across the trading dashboard."""

import numpy as np
from typing import Optional


def moving_average(data: list[float], window: int) -> list[Optional[float]]:
    """Simple Moving Average (SMA)."""
    result = [None] * len(data)
    for i in range(window - 1, len(data)):
        result[i] = sum(data[i - window + 1:i + 1]) / window
    return result


def exponential_moving_average(data: list[float], span: int) -> list[float]:
    """Exponential Moving Average (EMA)."""
    alpha = 2.0 / (span + 1)
    ema = [data[0]]
    for i in range(1, len(data)):
        ema.append(alpha * data[i] + (1 - alpha) * ema[-1])
    return ema


def rolling_std(data: list[float], window: int) -> list[Optional[float]]:
    """Rolling standard deviation."""
    result = [None] * len(data)
    for i in range(window - 1, len(data)):
        segment = data[i - window + 1:i + 1]
        result[i] = float(np.std(segment, ddof=1))
    return result


def z_score(value: float, mean: float, std: float) -> float:
    """Compute z-score."""
    if std == 0:
        return 0.0
    return (value - mean) / std


def percentile_rank(value: float, values: list[float]) -> float:
    """Compute percentile rank of a value within a distribution (0-100)."""
    if not values:
        return 50.0
    below = sum(1 for v in values if v < value)
    return round((below / len(values)) * 100, 1)


def compute_returns(prices: list[float]) -> list[float]:
    """Compute log returns from price series."""
    returns = []
    for i in range(1, len(prices)):
        if prices[i - 1] > 0:
            returns.append(np.log(prices[i] / prices[i - 1]))
        else:
            returns.append(0.0)
    return returns


def rolling_mean(data: list[float], window: int) -> list[Optional[float]]:
    """Rolling mean."""
    return moving_average(data, window)


def bollinger_bands(
    prices: list[float], window: int = 20, num_std: float = 2.0
) -> dict:
    """Compute Bollinger Bands."""
    sma = moving_average(prices, window)
    std = rolling_std(prices, window)

    upper = [None] * len(prices)
    lower = [None] * len(prices)
    width = [None] * len(prices)

    for i in range(len(prices)):
        if sma[i] is not None and std[i] is not None:
            upper[i] = sma[i] + num_std * std[i]
            lower[i] = sma[i] - num_std * std[i]
            width[i] = 2 * num_std * std[i]

    return {"sma": sma, "upper": upper, "lower": lower, "width": width, "std": std}


def normalize_min_max(values: list[float]) -> list[float]:
    """Min-max normalization to [0, 1]."""
    mn, mx = min(values), max(values)
    rng = mx - mn
    if rng == 0:
        return [0.5] * len(values)
    return [(v - mn) / rng for v in values]
