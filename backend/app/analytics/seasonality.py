"""Seasonality analytics — weekly/monthly seasonal patterns."""

import numpy as np
from typing import Optional


def weekly_seasonality(
    historical_prices: dict[int, list[float]], current_year: int = 2026
) -> dict:
    """
    Compute weekly seasonality: current year vs 5yr avg vs 10yr avg.
    
    historical_prices: {year: [52 weekly close prices]}
    """
    years = sorted(historical_prices.keys())
    current_data = historical_prices.get(current_year, [])
    recent_5 = [y for y in years if y != current_year and y >= current_year - 5]
    recent_10 = [y for y in years if y != current_year and y >= current_year - 10]

    data = []
    for week in range(52):
        point = {"week": f"W{week + 1}"}

        # Current year
        if week < len(current_data):
            point["current"] = round(current_data[week], 2)
        else:
            point["current"] = None

        # 5yr avg
        vals_5 = [historical_prices[y][week] for y in recent_5 if week < len(historical_prices.get(y, []))]
        point["avg5yr"] = round(float(np.mean(vals_5)), 2) if vals_5 else 0

        # 10yr avg
        vals_10 = [historical_prices[y][week] for y in recent_10 if week < len(historical_prices.get(y, []))]
        point["avg10yr"] = round(float(np.mean(vals_10)), 2) if vals_10 else 0

        data.append(point)

    return data


def monthly_returns_heatmap(
    monthly_prices: dict[int, list[float]], years: int = 5
) -> dict:
    """
    Compute monthly % returns heatmap.
    
    monthly_prices: {year: [12 monthly close prices]}
    Returns: {months: [str], years: [int], returns: [[float]]}
    """
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    all_years = sorted(monthly_prices.keys())[-years:]

    returns = []
    for year in all_years:
        prices = monthly_prices.get(year, [None] * 12)
        row = []
        for i in range(12):
            if i == 0 and year - 1 in monthly_prices:
                prev = monthly_prices[year - 1][-1] if monthly_prices[year - 1] else None
            elif i > 0:
                prev = prices[i - 1]
            else:
                prev = None

            curr = prices[i] if i < len(prices) else None
            if prev and curr and prev > 0:
                ret = ((curr - prev) / prev) * 100
                row.append(round(ret, 1))
            else:
                row.append(None)
        returns.append(row)

    return {"months": months, "years": all_years, "returns": returns}


def weekly_metrics(
    current_week_prices: list[float],
    historical_weekly_returns: list[float],
    current_week: int = 22,
) -> dict:
    """Compute weekly performance metrics vs historical."""
    if not current_week_prices or len(current_week_prices) < 2:
        return {
            "current_week": current_week,
            "current_perf": "+0.0%",
            "historical_median": "+0.0%",
            "deviation": "0.0σ",
            "banner": "neutral",
            "banner_text": "Insufficient data for seasonal analysis.",
        }

    perf = ((current_week_prices[-1] - current_week_prices[0]) / current_week_prices[0]) * 100
    median = float(np.median(historical_weekly_returns)) if historical_weekly_returns else 0
    std = float(np.std(historical_weekly_returns, ddof=1)) if len(historical_weekly_returns) > 1 else 1
    deviation = (perf - median) / std if std > 0 else 0

    banner = "bullish" if perf > median else "bearish"
    banner_text = (
        f"Current week trading {abs(deviation):.1f}σ {'above' if deviation > 0 else 'below'} "
        f"seasonal median. Historical week {current_week} is typically "
        f"{'positive' if median > 0 else 'negative'} ({median:+.1f}%)."
    )

    return {
        "current_week": current_week,
        "current_perf": f"{perf:+.1f}%",
        "historical_median": f"{median:+.1f}%",
        "deviation": f"{deviation:+.1f}σ",
        "banner": banner,
        "banner_text": banner_text,
    }
