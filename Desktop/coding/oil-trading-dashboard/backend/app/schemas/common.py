"""Common Pydantic schemas: DataProvenance, APIResponse, and shared types."""

from pydantic import BaseModel
from datetime import datetime
from typing import Any, Optional
from enum import Enum


class DataStatus(str, Enum):
    LIVE = "live"
    MOCK = "mock"
    STALE = "stale"
    DEGRADED = "degraded"


class DataProvenance(BaseModel):
    """Data source provenance — returned with every API response."""
    status: DataStatus
    source: str
    fetched_at: datetime
    cache_age_seconds: Optional[float] = None
    next_refresh_at: Optional[datetime] = None
    message: Optional[str] = None


class APIResponse(BaseModel):
    """Standard wrapper for ALL API responses."""
    data: Any
    provenance: DataProvenance


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    correlation_id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health endpoint response."""
    status: str
    uptime_seconds: float
    database: str
    redis: str
    adapters: dict[str, str]
    ws_connections: int
    version: str
