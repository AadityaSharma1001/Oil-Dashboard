"""FinBERT adapter — HTTP client to the FinBERT sidecar microservice."""

import httpx
import structlog
from app.adapters.base import DataAdapter, AdapterResult, SourceStatus
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class FinBERTAdapter(DataAdapter):
    def __init__(self):
        self.base_url = settings.finbert_service_url
        self.client = httpx.AsyncClient(timeout=30.0)

    @property
    def source_name(self) -> str:
        return "finbert"

    async def fetch(self, params: dict) -> AdapterResult:
        texts = params.get("texts", [])
        if not texts:
            return AdapterResult(data=[], status=SourceStatus.LIVE, source_name=self.source_name)
        try:
            resp = await self.client.post(
                f"{self.base_url}/analyze",
                json={"texts": texts},
            )
            resp.raise_for_status()
            return AdapterResult(
                data=resp.json(), status=SourceStatus.LIVE, source_name=self.source_name,
            )
        except Exception as e:
            logger.error("finbert_fetch_error", error=str(e))
            # Fallback: simple keyword-based sentiment
            results = []
            positive_kw = ["surge", "rally", "rise", "gain", "bullish", "cut", "draw", "recover"]
            negative_kw = ["fall", "drop", "decline", "bearish", "weak", "slump", "crash", "oversupply"]
            for text in texts:
                text_lower = text.lower()
                pos = sum(1 for kw in positive_kw if kw in text_lower)
                neg = sum(1 for kw in negative_kw if kw in text_lower)
                if pos > neg:
                    label, compound = "positive", 0.6
                elif neg > pos:
                    label, compound = "negative", -0.6
                else:
                    label, compound = "neutral", 0.0
                results.append({
                    "text": text, "label": label, "score": 0.7, "compound": compound,
                })
            return AdapterResult(
                data={"results": results, "model_version": "keyword-fallback", "inference_time_ms": 0},
                status=SourceStatus.DEGRADED, source_name=self.source_name,
                error_message=f"FinBERT unavailable, using keyword fallback: {str(e)}",
            )

    async def health_check(self) -> SourceStatus:
        try:
            resp = await self.client.get(f"{self.base_url}/health")
            data = resp.json()
            return SourceStatus.LIVE if data.get("model_loaded") else SourceStatus.DEGRADED
        except Exception:
            return SourceStatus.DOWN
