"""Sentiment analysis using VADER (fast) and FinBERT (heavy NLP)."""
from typing import Dict, List
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_vader = SentimentIntensityAnalyzer()

def finbert_ready() -> bool:
    return False

def classify(headline: str) -> Dict[str, object]:
    """Fast VADER sentiment. Returns compound and mapped label."""
    scores = _vader.polarity_scores(headline)
    compound = scores["compound"]
    
    if compound >= 0.05:
        label = "Bullish"
    elif compound <= -0.05:
        label = "Bearish"
    else:
        label = "Neutral"
        
    return {"label": label, "compound": compound}

def classify_finbert(headline: str) -> Dict[str, object]:
    """Fallback to VADER since local FinBERT is handled by microservice."""
    return classify(headline)

def aggregate(items: List[Dict[str, object]]) -> Dict[str, object]:
    """Aggregate sentiment over a list of news items."""
    if not items:
        return {"label": "Neutral", "score": 0.0, "bullish_pct": 0, "bearish_pct": 0}
        
    total = len(items)
    bullish = sum(1 for x in items if x.get("finbert_label", x.get("sentiment")) == "Bullish")
    bearish = sum(1 for x in items if x.get("finbert_label", x.get("sentiment")) == "Bearish")
    
    bullish_pct = int((bullish / total) * 100)
    bearish_pct = int((bearish / total) * 100)
    
    net = bullish - bearish
    if net > 0:
        label = "Bullish"
    elif net < 0:
        label = "Bearish"
    else:
        label = "Neutral"
        
    score = (net / total) * 100 # -100 to 100
    
    return {
        "label": label,
        "score": score,
        "bullish_pct": bullish_pct,
        "bearish_pct": bearish_pct
    }
