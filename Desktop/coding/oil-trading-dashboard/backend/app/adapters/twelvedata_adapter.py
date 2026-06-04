"""TwelveData adapter — real-time market data, intraday bars, technical indicators."""

import httpx
import structlog
from app.adapters.base import DataAdapter, AdapterResult, SourceStatus
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

TWELVEDATA_SYMBOLS = {
    "wti": "CL", "brent": "BZ", "rbob": "RB",
    "ho": "HO", "natgas": "NG", "gasoil": "QS",
}


class TwelveDataAdapter(DataAdapter):
    BASE_URL = "https://api.twelvedata.com"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0)

    @property
    def source_name(self) -> str:
        return "twelvedata"

    async def fetch(self, params: dict) -> AdapterResult:
        data_type = params.get("type", "quote")
        try:
            if data_type == "quote":
                return await self._fetch_quotes(params)
            elif data_type == "time_series":
                return await self._fetch_time_series(params)
            else:
                return self.get_mock_data(params)
        except Exception as e:
            logger.error("twelvedata_fetch_error", error=str(e))
            return AdapterResult(data=None, status=SourceStatus.DOWN, source_name=self.source_name, error_message=str(e))

    async def _fetch_quotes(self, params: dict) -> AdapterResult:
        symbols = params.get("symbols", list(TWELVEDATA_SYMBOLS.values()))
        symbol_str = ",".join(symbols)
        resp = await self.client.get(f"{self.BASE_URL}/quote", params={
            "symbol": symbol_str, "apikey": settings.twelvedata_api_key,
        })
        resp.raise_for_status()
        data = resp.json()
        return AdapterResult(data=data, status=SourceStatus.LIVE, source_name=self.source_name)

    async def _fetch_time_series(self, params: dict) -> AdapterResult:
        symbol = params.get("symbol", "CL")
        interval = params.get("interval", "1min")
        outputsize = params.get("outputsize", 390)
        resp = await self.client.get(f"{self.BASE_URL}/time_series", params={
            "symbol": symbol, "interval": interval,
            "outputsize": outputsize, "apikey": settings.twelvedata_api_key,
        })
        resp.raise_for_status()
        data = resp.json()
        values = data.get("values", [])
        if not values:
            return self.get_mock_data(params)
        return AdapterResult(data=values, status=SourceStatus.LIVE, source_name=self.source_name)

    async def health_check(self) -> SourceStatus:
        try:
            resp = await self.client.get(f"{self.BASE_URL}/quote", params={
                "symbol": "CL", "apikey": settings.twelvedata_api_key,
            })
            return SourceStatus.LIVE if resp.status_code == 200 else SourceStatus.DOWN
        except Exception:
            return SourceStatus.DOWN
