"""SQLAlchemy ORM models for all database tables."""

from datetime import datetime, date
from sqlalchemy import (
    Column, BigInteger, Integer, String, Numeric, Date, DateTime,
    Text, Index, UniqueConstraint, ForeignKey, JSON,
)
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base


class PriceHistory(Base):
    """Daily + intraday OHLCV for all commodities."""
    __tablename__ = "price_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)  # '1d', '1m', '5m'
    timestamp = Column(DateTime(timezone=True), nullable=False)
    open = Column(Numeric(12, 4))
    high = Column(Numeric(12, 4))
    low = Column(Numeric(12, 4))
    close = Column(Numeric(12, 4))
    volume = Column(BigInteger)
    source = Column(String(20), default="yahoo")

    __table_args__ = (
        UniqueConstraint("symbol", "timeframe", "timestamp"),
        Index("idx_price_symbol_time", "symbol", "timeframe", timestamp.desc()),
    )


class ForwardCurveSnapshot(Base):
    """Forward curve snapshots per commodity."""
    __tablename__ = "forward_curve_snapshot"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    commodity = Column(String(10), nullable=False)
    snapshot_date = Column(Date, nullable=False)
    tenor_month = Column(Integer, nullable=False)
    price = Column(Numeric(12, 4), nullable=False)
    source = Column(String(20), default="yahoo")

    __table_args__ = (
        UniqueConstraint("commodity", "snapshot_date", "tenor_month"),
    )


class Fundamental(Base):
    """EIA weekly/monthly fundamental indicators."""
    __tablename__ = "fundamentals"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    indicator = Column(String(50), nullable=False)
    report_date = Column(Date, nullable=False)
    value = Column(Numeric(14, 4), nullable=False)
    unit = Column(String(20))
    source = Column(String(20), default="eia")

    __table_args__ = (
        UniqueConstraint("indicator", "report_date"),
    )


class COTPositioning(Base):
    """CFTC COT weekly positioning data."""
    __tablename__ = "cot_positioning"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    commodity = Column(String(20), nullable=False)
    report_date = Column(Date, nullable=False)
    managed_money_long = Column(BigInteger)
    managed_money_short = Column(BigInteger)
    producer_long = Column(BigInteger)
    producer_short = Column(BigInteger)
    swap_dealer_long = Column(BigInteger)
    swap_dealer_short = Column(BigInteger)

    __table_args__ = (
        UniqueConstraint("commodity", "report_date"),
    )


class STEOProjection(Base):
    """EIA STEO monthly supply/demand projections."""
    __tablename__ = "steo_projection"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    publication_date = Column(Date, nullable=False)
    projection_month = Column(Date, nullable=False)
    world_supply = Column(Numeric(8, 2))
    world_demand = Column(Numeric(8, 2))
    opec_production = Column(Numeric(8, 2))
    non_opec_production = Column(Numeric(8, 2))

    __table_args__ = (
        UniqueConstraint("publication_date", "projection_month"),
    )


class HurricaneStorm(Base):
    """Active storm records from NHC."""
    __tablename__ = "hurricane_storm"

    id = Column(Integer, primary_key=True, autoincrement=True)
    storm_id = Column(String(20), unique=True, nullable=False)
    name = Column(String(50))
    category = Column(Integer)
    max_wind = Column(Integer)
    pressure = Column(Integer)
    movement = Column(String(50))
    lat = Column(Numeric(6, 2))
    lon = Column(Numeric(7, 2))
    status = Column(String(30))
    distance_to_shore = Column(Integer)
    last_updated = Column(DateTime(timezone=True), nullable=False)


class HurricaneTrackPoint(Base):
    """Storm track points (past + forecast)."""
    __tablename__ = "hurricane_track_point"

    id = Column(Integer, primary_key=True, autoincrement=True)
    storm_id = Column(String(20), ForeignKey("hurricane_storm.storm_id"), nullable=False)
    lon = Column(Numeric(7, 2))
    lat = Column(Numeric(6, 2))
    point_type = Column(String(10))  # past, current, forecast
    time_label = Column(String(10))
    category = Column(String(5))
    sort_order = Column(Integer)


class MacroIndicator(Base):
    """Macro economic indicators from FRED."""
    __tablename__ = "macro_indicator"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    indicator = Column(String(50), nullable=False)
    report_date = Column(Date, nullable=False)
    value = Column(String(20))
    source = Column(String(20), default="fred")

    __table_args__ = (
        UniqueConstraint("indicator", "report_date"),
    )


class SignalAudit(Base):
    """Full signal generation audit trail."""
    __tablename__ = "signal_audit"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    generated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    signal_version = Column(String(20), nullable=False)

    final_direction = Column(String(10), nullable=False)
    final_confidence = Column(Integer, nullable=False)
    conviction = Column(String(20))

    fundamental_score = Column(Numeric(6, 2))
    fundamental_max = Column(Numeric(6, 2))
    news_score = Column(Numeric(6, 2))
    news_max = Column(Numeric(6, 2))
    combined_score = Column(Numeric(6, 2))
    combined_max = Column(Numeric(6, 2))

    fundamental_signals = Column(JSONB)
    news_signals = Column(JSONB)
    trade_signals = Column(JSONB)
    input_snapshot = Column(JSONB)
    data_sources = Column(JSONB)
    market_state_at_generation = Column(JSONB)

    __table_args__ = (
        Index("idx_signal_audit_time", generated_at.desc()),
    )


class NewsArticle(Base):
    """Ingested news articles with FinBERT sentiment scores."""
    __tablename__ = "news_article"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source = Column(String(30), nullable=False)
    headline = Column(Text, nullable=False)
    summary = Column(Text)
    url = Column(Text)
    published_at = Column(DateTime(timezone=True))
    category = Column(String(30))
    finbert_label = Column(String(10))
    finbert_score = Column(Numeric(5, 4))
    finbert_compound = Column(Numeric(6, 4))
    impact_score = Column(Integer)
    ingested_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("source", "url"),
        Index("idx_news_published", published_at.desc()),
    )


class DataSourceStatus(Base):
    """Per-adapter live/mock/stale tracking."""
    __tablename__ = "data_source_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(String(30), unique=True, nullable=False)
    status = Column(String(15), nullable=False, default="live")
    last_success = Column(DateTime(timezone=True))
    last_failure = Column(DateTime(timezone=True))
    consecutive_failures = Column(Integer, default=0)
    last_error_message = Column(Text)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class ShippingChokepoint(Base):
    """Chokepoint transit data."""
    __tablename__ = "shipping_chokepoint"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    chokepoint = Column(String(30), nullable=False)
    observation_date = Column(Date, nullable=False)
    vessels_per_day = Column(Integer)
    volume_mbd = Column(Numeric(6, 2))
    avg_vessel_size_dwt = Column(Integer)
    source = Column(String(20))

    __table_args__ = (
        UniqueConstraint("chokepoint", "observation_date"),
    )


class FloatingStorageObs(Base):
    """Floating storage observations."""
    __tablename__ = "floating_storage"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_date = Column(Date, nullable=False)
    region = Column(String(30))
    total_mb = Column(Numeric(8, 2))
    vessel_count = Column(Integer)
    confidence_upper = Column(Numeric(8, 2))
    confidence_lower = Column(Numeric(8, 2))

    __table_args__ = (
        UniqueConstraint("observation_date", "region"),
    )


class VLCCRate(Base):
    """Tanker rate data by route."""
    __tablename__ = "vlcc_rates"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    route = Column(String(30), nullable=False)
    observation_date = Column(Date, nullable=False)
    worldscale_rate = Column(Numeric(8, 2))
    tce_usd_per_day = Column(Integer)
    source = Column(String(20))

    __table_args__ = (
        UniqueConstraint("route", "observation_date"),
    )
