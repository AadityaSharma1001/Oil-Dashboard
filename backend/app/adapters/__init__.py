"""Adapters module — unified data source integrations."""

from app.adapters.base import DataAdapter, AdapterResult, SourceStatus, AdapterRegistry, registry
from app.adapters.yahoo_adapter import YahooAdapter
from app.adapters.eia_adapter import EIAAdapter
from app.adapters.fred_adapter import FREDAdapter
from app.adapters.twelvedata_adapter import TwelveDataAdapter
from app.adapters.nhc_adapter import NHCAdapter
from app.adapters.oilprice_adapter import OilPriceAdapter
from app.adapters.cftc_adapter import CFTCAdapter
from app.adapters.shipping_adapter import ShippingAdapter
from app.adapters.finbert_adapter import FinBERTAdapter
from app.adapters.web_scraper import WebScrapingAdapter

def register_all_adapters():
    """Register all adapters and configure fallback chains."""
    registry.register(YahooAdapter())
    registry.register(TwelveDataAdapter())
    registry.register(EIAAdapter())
    registry.register(FREDAdapter())
    registry.register(NHCAdapter())
    registry.register(OilPriceAdapter())
    registry.register(CFTCAdapter())
    registry.register(ShippingAdapter())
    registry.register(FinBERTAdapter())
    registry.register(WebScrapingAdapter())

    # Configure fallback chains
    # realtime_prices: yahoo only (DXY fetched separately via TwelveData in router)
    registry.set_fallback_chain("realtime_prices", ["yahoo"])
    registry.set_fallback_chain("forward_curves", ["yahoo"])
    registry.set_fallback_chain("intraday_bars", ["twelvedata", "yahoo"])
    registry.set_fallback_chain("fundamentals", ["eia"])
    registry.set_fallback_chain("macro_data", ["fred"])
    registry.set_fallback_chain("hurricane_data", ["nhc"])
    registry.set_fallback_chain("cot_data", ["cftc"])
    registry.set_fallback_chain("news_data", ["oilprice"])
    registry.set_fallback_chain("sentiment", ["finbert"])
    registry.set_fallback_chain("shipping_data", ["shipping"])
    registry.set_fallback_chain("web_scraper", ["web_scraper"])


__all__ = [
    "DataAdapter", "AdapterResult", "SourceStatus", "AdapterRegistry",
    "registry", "register_all_adapters",
]
