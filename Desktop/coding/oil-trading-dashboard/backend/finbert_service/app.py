"""
FinBERT Sentiment Analysis Microservice.
Runs ProsusAI/finbert as a standalone FastAPI service.
"""

import time
from fastapi import FastAPI
from pydantic import BaseModel
import structlog

logger = structlog.get_logger()

app = FastAPI(title="FinBERT Sentiment Service", version="1.0.0")

# Model state
tokenizer = None
model = None
device = "cpu"


class SentimentRequest(BaseModel):
    texts: list[str]


class SentimentResult(BaseModel):
    text: str
    label: str        # positive, negative, neutral
    score: float      # Confidence 0-1
    compound: float   # Normalized -1 to +1


class SentimentResponse(BaseModel):
    results: list[SentimentResult]
    model_version: str
    inference_time_ms: float


@app.on_event("startup")
async def load_model():
    """Load FinBERT model at startup."""
    global tokenizer, model, device
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification

        logger.info("loading_finbert_model")
        tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
        model.eval()

        if torch.cuda.is_available():
            model = model.cuda()
            device = "cuda"
            logger.info("finbert_loaded_gpu")
        else:
            device = "cpu"
            logger.info("finbert_loaded_cpu")
    except Exception as e:
        logger.error("finbert_load_error", error=str(e))


@app.post("/analyze", response_model=SentimentResponse)
async def analyze_sentiment(request: SentimentRequest):
    """Batch sentiment analysis of financial text."""
    import torch

    if model is None or tokenizer is None:
        return SentimentResponse(
            results=[SentimentResult(text=t, label="neutral", score=0.5, compound=0.0) for t in request.texts],
            model_version="not_loaded", inference_time_ms=0,
        )

    start = time.time()

    inputs = tokenizer(
        request.texts, padding=True, truncation=True,
        max_length=512, return_tensors="pt",
    )
    if device == "cuda":
        inputs = {k: v.cuda() for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    probs = torch.softmax(outputs.logits, dim=1)
    labels = ["positive", "negative", "neutral"]

    results = []
    for i, text in enumerate(request.texts):
        scores = probs[i].cpu().tolist()
        best_idx = scores.index(max(scores))
        compound = scores[0] - scores[1]  # positive - negative
        results.append(SentimentResult(
            text=text,
            label=labels[best_idx],
            score=round(max(scores), 4),
            compound=round(compound, 4),
        ))

    elapsed = round((time.time() - start) * 1000, 2)
    logger.info("finbert_inference", batch_size=len(request.texts), time_ms=elapsed)

    return SentimentResponse(
        results=results,
        model_version="ProsusAI/finbert",
        inference_time_ms=elapsed,
    )


@app.get("/health")
async def health():
    """Health check — confirms model is loaded."""
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "device": device,
    }
