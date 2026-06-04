"""FRED API adapter — macroeconomic indicators."""

import httpx
import structlog
from app.adapters.base import DataAdapter, AdapterResult, SourceStatus
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

FRED_SERIES = {
    "us_pmi": "MANEMP",
    "china_pmi": "BSCICP03CNM665S",
    "eur_cpi": "CP0000EZ19M086NEST",
    "dxy": "DTWEXBGS",
    "fed_rate": "FEDFUNDS",
    "gdp": "GDP",
    "unemployment": "UNRATE",
    "cpi": "CPIAUCSL",
}


class FREDAdapter(DataAdapter):
    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=20.0)

    @property
    def source_name(self) -> str:
        return "fred"

    async def fetch(self, params: dict) -> AdapterResult:
        try:
            series_ids = params.get("series_ids", list(FRED_SERIES.values()))
            results = {}
            for name, sid in FRED_SERIES.items():
                if sid not in series_ids and name not in params.get("indicators", FRED_SERIES.keys()):
                    continue
                resp = await self.client.get(self.BASE_URL, params={
                    "series_id": sid, "api_key": settings.fred_api_key,
                    "file_type": "json", "sort_order": "desc", "limit": 5,
                })
                if resp.status_code == 200:
                    data = resp.json()
                    obs = data.get("observations", [])
                    if obs:
                        latest = obs[0]
                        prior = obs[1] if len(obs) > 1 else obs[0]
                        results[name] = {
                            "value": latest.get("value"),
                            "date": latest.get("date"),
                            "prior_value": prior.get("value"),
                        }
            if not results:
                return self.get_mock_data(params)
            return AdapterResult(data=results, status=SourceStatus.LIVE, source_name=self.source_name)
        except Exception as e:
            logger.error("fred_fetch_error", error=str(e))
            return AdapterResult(data=None, status=SourceStatus.DOWN, source_name=self.source_name, error_message=str(e))

    async def health_check(self) -> SourceStatus:
        try:
            resp = await self.client.get(self.BASE_URL, params={
                "series_id": "FEDFUNDS", "api_key": settings.fred_api_key,
                "file_type": "json", "sort_order": "desc", "limit": 1,
            })
            return SourceStatus.LIVE if resp.status_code == 200 else SourceStatus.DOWN
        except Exception:
            return SourceStatus.DOWN

    def get_mock_data(self, params: dict) -> AdapterResult:
        return AdapterResult(
            data={
                "us_pmi": {"value": "51.3", "date": "2026-05-01", "prior_value": "50.8"},
                "dxy": {"value": "104.2", "date": "2026-06-03", "prior_value": "103.8"},
            },
            status=SourceStatus.MOCK, source_name=self.source_name,
            error_message="FRED API unavailable — returning mock data",
        )
