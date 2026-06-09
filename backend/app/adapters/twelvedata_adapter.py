"""TwelveData adapter — real-time market data for DXY and other instruments."""

import httpx
import structlog
from app.adapters.base import DataAdapter, AdapterResult, SourceStatus
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# DXY and additional instruments fetched via TwelveData
TWELVEDATA_SYMBOLS = {
    "dxy": {"symbol": "DXY", "label": "DXY", "exchange": ""},
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
            elif data_type == "tickers":
                return await self._fetch_ticker_format(params)
            elif data_type == "time_series":
                return await self._fetch_time_series(params)
            else:
                return self.get_mock_data(params)
        except Exception as e:
            logger.error("twelvedata_fetch_error", error=str(e))
            return AdapterResult(data=None, status=SourceStatus.DOWN, source_name=self.source_name, error_message=str(e))

    async def _fetch_quotes(self, params: dict) -> AdapterResult:
        """Raw quote data from TwelveData."""
        symbols = params.get("symbols", [info["symbol"] for info in TWELVEDATA_SYMBOLS.values()])
        symbol_str = ",".join(symbols)
        resp = await self.client.get(f"{self.BASE_URL}/quote", params={
            "symbol": symbol_str, "apikey": settings.twelvedata_api_key,
        })
        resp.raise_for_status()
        data = resp.json()
        return AdapterResult(data=data, status=SourceStatus.LIVE, source_name=self.source_name)

    async def _fetch_ticker_format(self, params: dict) -> AdapterResult:
        """Fetch DXY (and other instruments) formatted as ticker objects
        matching the frontend's expected shape: { id, label, price, change, pct }."""
        result = []

        for key, info in TWELVEDATA_SYMBOLS.items():
            try:
                resp = await self.client.get(f"{self.BASE_URL}/quote", params={
                    "symbol": info["symbol"],
                    "apikey": settings.twelvedata_api_key,
                })
                if resp.status_code != 200:
                    continue

                data = resp.json()
                if "code" in data and data["code"] != 200:
                    # API error
                    logger.warning("twelvedata_quote_error", symbol=info["symbol"], response=data)
                    continue

                price = float(data.get("close", 0))
                prev_close = float(data.get("previous_close", price))
                change = price - prev_close
                pct = (change / prev_close * 100) if prev_close != 0 else 0

                result.append({
                    "id": key,
                    "label": info["label"],
                    "price": round(price, 2),
                    "change": round(change, 2),
                    "pct": f"{'+' if pct >= 0 else ''}{pct:.2f}%",
                })
            except Exception as e:
                logger.warning("twelvedata_ticker_error", symbol=key, error=str(e))

        if not result:
            return self.get_mock_data(params)

        return AdapterResult(data=result, status=SourceStatus.LIVE, source_name=self.source_name)

    async def _fetch_time_series(self, params: dict) -> AdapterResult:
        symbol = params.get("symbol", "DXY")
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
                "symbol": "DXY", "apikey": settings.twelvedata_api_key,
            })
            return SourceStatus.LIVE if resp.status_code == 200 else SourceStatus.DOWN
        except Exception:
            return SourceStatus.DOWN

    def get_mock_data(self, params: dict) -> AdapterResult:
        """Return mock ticker data for TwelveData instruments."""
        data_type = params.get("type", "tickers")
        if data_type == "tickers":
            return AdapterResult(
                data=[
                    {"id": "dxy", "label": "DXY", "price": 104.21, "change": -0.32, "pct": "-0.31%"},
                ],
                status=SourceStatus.MOCK,
                source_name=self.source_name,
                error_message="TwelveData unavailable — returning mock data",
            )
        return super().get_mock_data(params)
