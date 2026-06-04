"""Pydantic schemas for all API endpoints."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Tickers ──
class TickerItem(BaseModel):
    id: str
    label: str
    price: float
    change: float
    pct: str


class TickersResponse(BaseModel):
    tickers: list[TickerItem]


# ── Forward Curves ──
class ForwardCurvePoint(BaseModel):
    month: str
    current: float
    avg5yr: float


class ForwardCurveResponse(BaseModel):
    commodity: str
    data: list[ForwardCurvePoint]


# ── Intraday VWAP ──
class IntradayBar(BaseModel):
    time: str
    price: float
    vwap: float
    upper_band: float
    lower_band: float
    band_width: float
    deviation: float
    volume: int


class IntradayResponse(BaseModel):
    commodity: str
    data: list[IntradayBar]
    last_vwap: float
    last_band_width: float
    last_deviation: float


# ── Spreads ──
class SpreadPoint(BaseModel):
    day: str
    value: float
    mean: float
    hi: float
    lo: float


class CalendarSpreadResponse(BaseModel):
    commodity: str
    tenor: str
    data: list[SpreadPoint]


class FlyPoint(BaseModel):
    label: str
    value: float
    mean: float
    hi: float
    lo: float


class FlyResponse(BaseModel):
    commodity: str
    term_structure: list[FlyPoint]
    history: list[dict]


class M1M12Point(BaseModel):
    day: str
    wti: float
    brent: float


class M1M12Response(BaseModel):
    data: list[M1M12Point]
    threshold: float


# ── 5-Year Range ──
class RangePoint(BaseModel):
    day: str
    high5yr: float
    low5yr: float
    mean5yr: float
    open: Optional[float] = None
    close: Optional[float] = None


class FiveYearRangeResponse(BaseModel):
    commodity: str
    data: list[RangePoint]
    current_price: float
    mean_price: float
    vs_mean: float
    percentile: int


# ── Core Desk ──
class CovarianceResponse(BaseModel):
    labels: list[str]
    values: list[list[float]]
    highlights: list[list[int]]


class PCAComponent(BaseModel):
    label: str
    pct: float
    color: str
    spark: list[float]


class PCAResponse(BaseModel):
    commodity: str
    components: list[PCAComponent]


class CorrelationPoint(BaseModel):
    day: str
    correlation: float


class DollarCorrelationResponse(BaseModel):
    data: list[CorrelationPoint]
    current: float


class ArbPoint(BaseModel):
    day: str
    spread: float
    upper: float
    lower: float
    mean: float


class ArbResponse(BaseModel):
    data: list[ArbPoint]
    current_spread: float
    mean_30d: float
    std_30d: float
    z_score: float


class DifferentialItem(BaseModel):
    grade: str
    value: float


class DifferentialsResponse(BaseModel):
    data: list[DifferentialItem]


# ── Crack Spreads ──
class CrackSpreadItem(BaseModel):
    name: str
    current: float
    avg5yr: float
    deviation: float
    deviation_pct: float


class CrackSpreadsResponse(BaseModel):
    data: list[CrackSpreadItem]


# ── Fundamentals ──
class FundamentalCard(BaseModel):
    id: str
    label: str
    value: str
    unit: str
    change: Optional[float] = None
    avg5yr: Optional[str] = None
    direction: Optional[str] = None


class FundamentalsCardsResponse(BaseModel):
    cards: list[FundamentalCard]


class CushingPoint(BaseModel):
    week: str
    stock: float
    avg5yr: float


class CushingResponse(BaseModel):
    utilization: float
    data: list[CushingPoint]


class FloatingStoragePoint(BaseModel):
    day: str
    central: float
    upper: float
    lower: float


class FloatingStorageResponse(BaseModel):
    data: list[FloatingStoragePoint]


# ── Signals ──
class FundamentalSignal(BaseModel):
    indicator: str
    trend: str
    type: str
    strength: str
    impact: str
    score: float


class NewsSignal(BaseModel):
    category: str
    score: float
    type: str
    top_headline: str


class TradeSignalItem(BaseModel):
    id: int
    name: str
    direction: str
    confidence: int
    rationale: str


class SignalEngineResponse(BaseModel):
    final_direction: str
    final_confidence: int
    conviction: str
    fundamental_score: float
    fundamental_max: float
    news_score: float
    news_max: float
    combined_score: float
    combined_max: float
    fundamental_signals: list[FundamentalSignal]
    news_signals: list[NewsSignal]
    top_driver: Optional[str] = None
    top_risk: Optional[str] = None
    bullish_power: float
    bearish_power: float


class TradeSignalsResponse(BaseModel):
    signals: list[TradeSignalItem]
    buy_count: int
    sell_count: int
    hold_count: int


class SignalAuditRecord(BaseModel):
    id: int
    generated_at: datetime
    signal_version: str
    final_direction: str
    final_confidence: int
    conviction: str
    fundamental_score: float
    news_score: float
    combined_score: float
    data_sources: dict


class SignalAuditResponse(BaseModel):
    records: list[SignalAuditRecord]
    total: int


# ── Sentiment ──
class SentimentItem(BaseModel):
    headline: str
    source: str
    published_at: Optional[datetime] = None
    category: Optional[str] = None
    label: str
    score: float
    compound: float
    impact_score: Optional[int] = None


class SentimentLatestResponse(BaseModel):
    articles: list[SentimentItem]


class SentimentAggregateItem(BaseModel):
    category: str
    avg_compound: float
    article_count: int
    bias: str


class SentimentAggregateResponse(BaseModel):
    aggregates: list[SentimentAggregateItem]
    overall_compound: float
    overall_bias: str


# ── COT ──
class COTPoint(BaseModel):
    week: str
    managed_money: int
    producer: int
    swap_dealer: int
    net_spec: int


class COTResponse(BaseModel):
    data: list[COTPoint]


# ── Freight ──
class BDTIPoint(BaseModel):
    day: str
    value: float


class BDTIResponse(BaseModel):
    data: list[BDTIPoint]
    current: float
    change_30d: float
    change_30d_pct: float


# ── Shipping ──
class ChokepointData(BaseModel):
    name: str
    vessels_per_day: int
    volume_mbd: float
    avg_30d_vessels: Optional[float] = None
    yoy_change_pct: Optional[float] = None


class ChokepointsResponse(BaseModel):
    chokepoints: list[ChokepointData]


class FloatingStorageRegion(BaseModel):
    region: str
    total_mb: float
    vessel_count: int
    confidence_upper: float
    confidence_lower: float


class ShippingFloatingStorageResponse(BaseModel):
    global_total_mb: float
    regions: list[FloatingStorageRegion]


class VLCCRateItem(BaseModel):
    route: str
    worldscale_rate: float
    tce_usd_per_day: int


class VLCCRatesResponse(BaseModel):
    rates: list[VLCCRateItem]


# ── STEO ──
class STEOPoint(BaseModel):
    month: str
    supply: float
    demand: float
    balance: float
    opec: float
    non_opec: float


class STEOResponse(BaseModel):
    data: list[STEOPoint]


# ── Hurricanes ──
class StormTrackPoint(BaseModel):
    lon: float
    lat: float
    type: str
    time: str
    cat: str


class ActiveStorm(BaseModel):
    id: str
    name: str
    category: int
    wind: int
    pressure: int
    movement: str
    location: dict
    status: str
    distance_to_shore: int
    track: list[StormTrackPoint]


class SeasonSummary(BaseModel):
    year: int
    named_storms: int
    hurricanes: int
    major_hurricanes: int
    ace_index: float


class PlatformStatus(BaseModel):
    name: str
    lat: float
    lon: float
    status: str
    capacity: float


class InfrastructureImpact(BaseModel):
    platforms_shut_in: int
    platforms_total: int
    production_offline: float
    production_total: float
    ref_capacity_at_risk: float
    ref_capacity_total: float
    ports_closed: list[str]
    ports_open: int


class HurricaneActiveResponse(BaseModel):
    season: SeasonSummary
    active_storms: list[ActiveStorm]
    infrastructure: InfrastructureImpact
    gulf_platforms: list[PlatformStatus]


# ── Macro ──
class SeasonalityPoint(BaseModel):
    week: str
    current: Optional[float] = None
    avg5yr: float
    avg10yr: float


class SeasonalityResponse(BaseModel):
    commodity: str
    data: list[SeasonalityPoint]


class HeatmapResponse(BaseModel):
    months: list[str]
    years: list[int]
    returns: list[list[Optional[float]]]


class WeeklyMetrics(BaseModel):
    current_week: int
    current_perf: str
    historical_median: str
    deviation: str
    banner: str
    banner_text: str


class MacroTableRow(BaseModel):
    indicator: str
    latest: str
    prior: str


class MacroResponse(BaseModel):
    spare_capacity: list[dict]
    macro_table: list[MacroTableRow]


# ── News ──
class NewsItem(BaseModel):
    id: int
    time: str
    headline: str
    category: str
    impact: str
    type: str


class NewsResponse(BaseModel):
    items: list[NewsItem]
    keyword_data: Optional[list[dict]] = None
