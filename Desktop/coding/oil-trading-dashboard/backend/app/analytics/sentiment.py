"""Sentiment analysis using VADER (fast) and FinBERT (heavy NLP)."""
from typing import Dict, List
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_vader = SentimentIntensityAnalyzer()
_finbert_pipeline = None
_finbert_is_ready = False

def init_finbert():
    """Load FinBERT model into memory. Call this during app startup."""
    global _finbert_pipeline, _finbert_is_ready
    try:
        from transformers import pipeline
        _finbert_pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert")
        _finbert_is_ready = True
    except Exception as e:
        import structlog
        structlog.get_logger().error("Failed to init FinBERT", error=str(e))

def finbert_ready() -> bool:
    return _finbert_is_ready

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
    """FinBERT NLP sentiment. Maps positive->Bullish, negative->Bearish."""
    if not _finbert_is_ready or _finbert_pipeline is None:
        return classify(headline)
        
    try:
        res = _finbert_pipeline(headline)[0]
        flabel = res["label"].lower()
        score = res["score"] # confidence 0.0 to 1.0
        
        # map finbert to our nomenclature
        if flabel == "positive":
            label = "Bullish"
            compound = score
        elif flabel == "negative":
            label = "Bearish"
            compound = -score
        else:
            label = "Neutral"
            compound = 0.0
            
        return {"label": label, "compound": compound}
    except Exception:
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
