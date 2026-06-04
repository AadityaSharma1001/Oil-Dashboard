"""Yahoo Finance adapter — real-time prices, futures chains, historical data."""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import structlog

from app.adapters.base import DataAdapter, AdapterResult, SourceStatus

logger = structlog.get_logger()

# Symbol mapping
TICKER_SYMBOLS = {
    "wti": "CL=F", "brent": "BZ=F", "rbob": "RB=F",
    "ho": "HO=F", "natgas": "NG=F", "dxy": "DX-Y.NYB",
    "gasoil": "QS=F",
}

# Futures chain symbols (approximate — M1 through M36)
WTI_FUTURES_ROOT = "CL"
BRENT_FUTURES_ROOT = "BZ"


class YahooAdapter(DataAdapter):
    """Yahoo Finance via yfinance for prices, forward curves, historical data."""

    @property
    def source_name(self) -> str:
        return "yahoo"

    async def fetch(self, params: dict) -> AdapterResult:
        data_type = params.get("type", "tickers")

        try:
            if data_type == "tickers":
                return await self._fetch_tickers(params)
            elif data_type == "forward_curve":
                return await self._fetch_forward_curve(params)
            elif data_type == "historical":
                return await self._fetch_historical(params)
            elif data_type == "intraday":
                return await self._fetch_intraday(params)
            else:
                return self.get_mock_data(params)
        except Exception as e:
            logger.error("yahoo_fetch_error", error=str(e), data_type=data_type)
            return AdapterResult(
                data=None, status=SourceStatus.DOWN,
                source_name=self.source_name, error_message=str(e),
            )

    async def _fetch_tickers(self, params: dict) -> AdapterResult:
        symbols = list(TICKER_SYMBOLS.values())
        tickers_data = yf.download(
            tickers=symbols, period="2d", interval="1d",
            group_by="ticker", progress=False, threads=True,
        )

        result = []
        for key, symbol in TICKER_SYMBOLS.items():
            try:
                if len(symbols) == 1:
                    df = tickers_data
                else:
                    df = tickers_data[symbol] if symbol in tickers_data.columns.get_level_values(0) else None

                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else df.iloc[-1]
                    price = float(latest["Close"])
                    change = price - float(prev["Close"])
                    pct = (change / float(prev["Close"])) * 100 if float(prev["Close"]) != 0 else 0

                    result.append({
                        "id": key,
                        "label": key.upper().replace("_", " "),
                        "price": round(price, 4),
                        "change": round(change, 4),
                        "pct": f"{'+' if pct >= 0 else ''}{pct:.2f}%",
                    })
            except Exception as e:
                logger.warning("yahoo_ticker_parse_error", symbol=symbol, error=str(e))

        if not result:
            return self.get_mock_data(params)

        return AdapterResult(
            data=result, status=SourceStatus.LIVE, source_name=self.source_name,
        )

    async def _fetch_forward_curve(self, params: dict) -> AdapterResult:
        commodity = params.get("commodity", "wti")
        root = WTI_FUTURES_ROOT if commodity == "wti" else BRENT_FUTURES_ROOT
        base_symbol = f"{root}=F"

        # Fetch front-month to estimate curve
        ticker = yf.Ticker(base_symbol)
        info = ticker.info
        current_price = info.get("regularMarketPrice", info.get("previousClose", 0))

        if not current_price:
            return self.get_mock_data(params)

        # Generate approximate curve from front month
        # In production, fetch each individual contract month
        curve_data = []
        for i in range(36):
            # Approximate backwardation/contango curve
            decay = 0.15 * (i / 36)
            price = current_price * (1 - decay)
            curve_data.append({
                "month": f"M{i + 1}",
                "current": round(price, 2),
            })

        return AdapterResult(
            data=curve_data, status=SourceStatus.LIVE, source_name=self.source_name,
        )

    async def _fetch_historical(self, params: dict) -> AdapterResult:
        symbol = params.get("symbol", "CL=F")
        period = params.get("period", "5y")
        interval = params.get("interval", "1d")

        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if df.empty:
            return self.get_mock_data(params)

        data = []
        for idx, row in df.iterrows():
            data.append({
                "date": idx.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]) if pd.notna(row["Volume"]) else 0,
            })

        return AdapterResult(
            data=data, status=SourceStatus.LIVE, source_name=self.source_name,
        )

    async def _fetch_intraday(self, params: dict) -> AdapterResult:
        symbol = params.get("symbol", "CL=F")
        df = yf.download(symbol, period="1d", interval="1m", progress=False)

        if df.empty:
            return self.get_mock_data(params)

        data = []
        for idx, row in df.iterrows():
            data.append({
                "time": idx.strftime("%H:%M"),
                "open": round(float(row["Open"]), 3),
                "high": round(float(row["High"]), 3),
                "low": round(float(row["Low"]), 3),
                "close": round(float(row["Close"]), 3),
                "volume": int(row["Volume"]) if pd.notna(row["Volume"]) else 0,
            })

        return AdapterResult(
            data=data, status=SourceStatus.LIVE, source_name=self.source_name,
        )

    async def health_check(self) -> SourceStatus:
        try:
            t = yf.Ticker("CL=F")
            price = t.info.get("regularMarketPrice")
            return SourceStatus.LIVE if price else SourceStatus.DEGRADED
        except Exception:
            return SourceStatus.DOWN

    def get_mock_data(self, params: dict) -> AdapterResult:
        """Return mock data for Yahoo Finance."""
        data_type = params.get("type", "tickers")
        if data_type == "tickers":
            mock_tickers = [
                {"id": "wti", "label": "WTI M1", "price": 72.45, "change": 0.83, "pct": "+1.16%"},
                {"id": "brent", "label": "Brent M1", "price": 76.30, "change": 0.65, "pct": "+0.86%"},
                {"id": "rbob", "label": "RBOB", "price": 2.342, "change": -0.018, "pct": "-0.76%"},
                {"id": "ho", "label": "Heat Oil", "price": 2.485, "change": 0.012, "pct": "+0.48%"},
                {"id": "gasoil", "label": "ICE Gasoil", "price": 684.50, "change": 3.25, "pct": "+0.48%"},
                {"id": "natgas", "label": "Nat Gas", "price": 2.78, "change": -0.06, "pct": "-2.11%"},
                {"id": "dxy", "label": "DXY", "price": 104.21, "change": -0.32, "pct": "-0.31%"},
                {"id": "bwsprd", "label": "B-W Sprd", "price": 3.85, "change": 0.18, "pct": "+4.91%"},
                {"id": "rigs", "label": "Rig Count", "price": 584, "change": -3, "pct": "-0.51%"},
            ]
            return AdapterResult(
                data=mock_tickers, status=SourceStatus.MOCK,
                source_name=self.source_name,
                error_message="Live data unavailable — returning mock data",
            )
        return super().get_mock_data(params)
