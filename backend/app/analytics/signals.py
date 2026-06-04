"""Signal scoring algorithms — fundamental + news + trade signal computation."""

from typing import Optional
import numpy as np


# Weight configuration for fundamental indicators
FUNDAMENTAL_WEIGHTS = {
    "us_crude_stocks": {"weight": 3.0, "bullish_if": "falling"},
    "cushing_inventory": {"weight": 2.5, "bullish_if": "falling"},
    "us_production": {"weight": 2.0, "bullish_if": "falling"},
    "refinery_utilization": {"weight": 2.0, "bullish_if": "rising"},
    "spr_level": {"weight": 1.5, "bullish_if": "falling"},
    "rig_count": {"weight": 1.5, "bullish_if": "falling"},
    "opec_production": {"weight": 2.5, "bullish_if": "falling"},
    "us_pmi": {"weight": 1.5, "bullish_if": "rising"},
    "dxy": {"weight": 2.0, "bullish_if": "falling"},
    "crack_spread_3_2_1": {"weight": 2.0, "bullish_if": "rising"},
    "net_imports": {"weight": 1.0, "bullish_if": "rising"},
    "hormuz_traffic": {"weight": 1.0, "bullish_if": "falling"},
}


def score_fundamental_indicator(
    indicator: str, current: float, prior: float
) -> dict:
    """Score a single fundamental indicator."""
    config = FUNDAMENTAL_WEIGHTS.get(indicator, {"weight": 1.0, "bullish_if": "rising"})
    weight = config["weight"]
    change = current - prior

    is_bullish = (change < 0) if config["bullish_if"] == "falling" else (change > 0)
    trend = "Draws" if config["bullish_if"] == "falling" and change < 0 else \
            "Builds" if config["bullish_if"] == "falling" and change > 0 else \
            "Rising" if change > 0 else "Falling"

    abs_change = abs(change) / (abs(prior) + 1e-10) * 100
    if abs_change > 2:
        strength = "strong"
    elif abs_change > 0.5:
        strength = "moderate"
    else:
        strength = "weak"

    score = weight * (1 if is_bullish else -1) * min(abs_change / 2, 1.5)

    return {
        "indicator": indicator,
        "trend": trend,
        "type": "bullish" if is_bullish else "bearish",
        "strength": strength,
        "impact": f"{'↑' if is_bullish else '↓'} {abs_change:.1f}%",
        "score": round(score, 2),
    }


def score_news_sentiment(articles: list[dict]) -> list[dict]:
    """Score news articles by category."""
    category_scores = {}
    for article in articles:
        cat = article.get("category", "General")
        compound = article.get("finbert_compound", article.get("compound", 0))
        if cat not in category_scores:
            category_scores[cat] = {"total": 0, "count": 0, "top": article.get("headline", "")}
        category_scores[cat]["total"] += compound
        category_scores[cat]["count"] += 1

    results = []
    for cat, data in category_scores.items():
        avg = data["total"] / data["count"] if data["count"] > 0 else 0
        score = avg * 2  # Scale -2 to +2
        results.append({
            "category": cat,
            "score": round(score, 2),
            "type": "bullish" if score > 0 else "bearish",
            "top_headline": data["top"],
        })

    return results


def compute_trade_signals(
    fundamentals: dict, cracks: list[dict], spreads: dict, macro: dict
) -> list[dict]:
    """Generate individual trade signal cards."""
    signals = []

    # Signal 1: WTI-Brent Statistical Arbitrage
    bw_spread = spreads.get("bw_mean", 3.85)
    bw_std = spreads.get("bw_std", 0.45)
    bw_z = spreads.get("bw_z_score", 0)
    if abs(bw_z) > 1.5:
        direction = "SELL" if bw_z > 0 else "BUY"
        signals.append({
            "id": 1, "name": "WTI-Brent Stat-Arb",
            "direction": direction,
            "confidence": min(95, int(50 + abs(bw_z) * 15)),
            "rationale": f"Brent-WTI spread at {bw_z:.1f}σ deviation from 30d mean. Mean-reversion probability elevated.",
        })
    else:
        signals.append({
            "id": 1, "name": "WTI-Brent Stat-Arb",
            "direction": "HOLD", "confidence": 35,
            "rationale": f"Spread within normal range ({bw_z:.1f}σ). No edge.",
        })

    # Signal 2: Crack Spread Signal
    crack = cracks[0] if cracks else {"current": 28, "avg5yr": 28.5}
    crack_dev = (crack["current"] - crack["avg5yr"]) / crack["avg5yr"] * 100
    if crack_dev > 10:
        signals.append({"id": 2, "name": "3:2:1 Crack Divergence", "direction": "BUY", "confidence": 72, "rationale": f"Crack spreads {crack_dev:.1f}% above 5yr avg. Strong refinery margins signal robust demand."})
    elif crack_dev < -10:
        signals.append({"id": 2, "name": "3:2:1 Crack Divergence", "direction": "SELL", "confidence": 68, "rationale": f"Crack spreads {crack_dev:.1f}% below 5yr avg. Weak margins indicate oversupply in products."})
    else:
        signals.append({"id": 2, "name": "3:2:1 Crack Divergence", "direction": "HOLD", "confidence": 40, "rationale": "Crack spreads near 5yr norm."})

    # Signal 3: Inventory Signal
    stocks_change = fundamentals.get("us_crude_stocks", {}).get("change", 0)
    if stocks_change < -3:
        signals.append({"id": 3, "name": "US Crude Inventory Surprise", "direction": "BUY", "confidence": 78, "rationale": f"Large draw of {abs(stocks_change):.1f}mb exceeds expectations. Bullish supply signal."})
    elif stocks_change > 3:
        signals.append({"id": 3, "name": "US Crude Inventory Surprise", "direction": "SELL", "confidence": 70, "rationale": f"Build of {stocks_change:.1f}mb signals supply surplus."})
    else:
        signals.append({"id": 3, "name": "US Crude Inventory Surprise", "direction": "HOLD", "confidence": 45, "rationale": "Inventory change within expected range."})

    # Signal 4: Contango/Backwardation
    m1m12 = spreads.get("m1m12_current", 0.5)
    if m1m12 > 2:
        signals.append({"id": 4, "name": "Term Structure Backwardation", "direction": "BUY", "confidence": 65, "rationale": f"Strong backwardation (${m1m12:.2f}/bbl). Market pricing near-term tightness."})
    elif m1m12 < -1:
        signals.append({"id": 4, "name": "Term Structure Contango", "direction": "SELL", "confidence": 62, "rationale": f"Contango (${m1m12:.2f}/bbl). Market signals oversupply."})
    else:
        signals.append({"id": 4, "name": "Term Structure Signal", "direction": "HOLD", "confidence": 40, "rationale": "Flat structure — no strong directional bias."})

    # Signal 5: DXY Correlation Signal
    dxy_change = float(macro.get("dxy", {}).get("change", 0) or 0)
    if dxy_change < -0.5:
        signals.append({"id": 5, "name": "Dollar Weakness Signal", "direction": "BUY", "confidence": 60, "rationale": "USD weakening supports commodity prices."})
    elif dxy_change > 0.5:
        signals.append({"id": 5, "name": "Dollar Strength Signal", "direction": "SELL", "confidence": 58, "rationale": "USD strength headwind for commodities."})
    else:
        signals.append({"id": 5, "name": "Dollar Neutral", "direction": "HOLD", "confidence": 35, "rationale": "DXY within normal range."})

    # Signal 6: Seasonal Pattern
    signals.append({"id": 6, "name": "Seasonal Pattern", "direction": "BUY", "confidence": 55, "rationale": "Historically bullish period for crude. June draws typical as driving season demand kicks in."})

    # Signal 7: OPEC Compliance
    signals.append({"id": 7, "name": "OPEC+ Compliance", "direction": "BUY", "confidence": 62, "rationale": "OPEC+ voluntary cuts holding. Compliance rate >90% supports price floor."})

    return signals


def compute_final_signal(
    fundamental_signals: list[dict], news_signals: list[dict]
) -> dict:
    """Compute the final composite trading signal."""
    fun_score = sum(s["score"] for s in fundamental_signals)
    fun_max = sum(abs(s["score"]) for s in fundamental_signals) or 1
    news_score = sum(s["score"] for s in news_signals)
    news_max = sum(abs(s["score"]) for s in news_signals) or 1

    # Combined: 70% fundamentals, 30% news
    combined = 0.7 * fun_score + 0.3 * news_score
    combined_max = 0.7 * fun_max + 0.3 * news_max

    confidence = int(abs(combined / combined_max) * 100) if combined_max > 0 else 50

    if combined > 2:
        direction = "BUY"
    elif combined > 0.5:
        direction = "LEAN_BUY"
    elif combined < -2:
        direction = "SELL"
    elif combined < -0.5:
        direction = "LEAN_SELL"
    else:
        direction = "NEUTRAL"

    if confidence >= 70:
        conviction = "High"
    elif confidence >= 45:
        conviction = "Medium"
    else:
        conviction = "Low"

    bullish = sum(s["score"] for s in fundamental_signals if s["score"] > 0)
    bearish = abs(sum(s["score"] for s in fundamental_signals if s["score"] < 0))

    top_driver = max(fundamental_signals, key=lambda s: s["score"])["indicator"] if fundamental_signals else None
    top_risk = min(fundamental_signals, key=lambda s: s["score"])["indicator"] if fundamental_signals else None

    return {
        "final_direction": direction,
        "final_confidence": confidence,
        "conviction": conviction,
        "fundamental_score": round(fun_score, 2),
        "fundamental_max": round(fun_max, 2),
        "news_score": round(news_score, 2),
        "news_max": round(news_max, 2),
        "combined_score": round(combined, 2),
        "combined_max": round(combined_max, 2),
        "bullish_power": round(bullish, 2),
        "bearish_power": round(bearish, 2),
        "top_driver": top_driver,
        "top_risk": top_risk,
    }
