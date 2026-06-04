"""Unified adapter architecture — base class and registry for all data sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Any, Optional
import structlog

logger = structlog.get_logger()


class SourceStatus(str, Enum):
    LIVE = "live"
    STALE = "stale"
    MOCK = "mock"
    DEGRADED = "degraded"
    DOWN = "down"


@dataclass
class AdapterResult:
    """Every adapter call returns this envelope."""
    data: Any
    status: SourceStatus
    source_name: str
    fetched_at: datetime = field(default_factory=datetime.utcnow)
    cache_age_seconds: Optional[float] = None
    next_refresh_at: Optional[datetime] = None
    error_message: Optional[str] = None


class DataAdapter(ABC):
    """Abstract contract every data source integration must implement."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier, e.g. 'eia', 'yahoo', 'nhc'."""

    @abstractmethod
    async def fetch(self, params: dict) -> AdapterResult:
        """Fetch data from the source. Must return AdapterResult with status."""

    @abstractmethod
    async def health_check(self) -> SourceStatus:
        """Lightweight connectivity probe. Called by /health."""

    def get_mock_data(self, params: dict) -> AdapterResult:
        """Return synthetic fallback. Override per-adapter for richer mocks."""
        return AdapterResult(
            data=None,
            status=SourceStatus.MOCK,
            source_name=self.source_name,
            error_message="Live data unavailable — returning mock data",
        )


class AdapterRegistry:
    """
    Runtime registry for all adapters.
    Enables discovery, fallback chains, and health aggregation.
    """

    def __init__(self):
        self._adapters: dict[str, DataAdapter] = {}
        self._fallback_chains: dict[str, list[str]] = {}

    def register(self, adapter: DataAdapter):
        """Register an adapter by its source_name."""
        self._adapters[adapter.source_name] = adapter
        logger.info("adapter_registered", adapter=adapter.source_name)

    def get(self, name: str) -> Optional[DataAdapter]:
        """Get a specific adapter by name."""
        return self._adapters.get(name)

    def set_fallback_chain(self, data_type: str, adapter_names: list[str]):
        """
        Configure ordered fallback chain for a data type.
        e.g. set_fallback_chain('realtime_prices', ['twelvedata', 'yahoo'])
        """
        self._fallback_chains[data_type] = adapter_names

    async def fetch_with_fallback(self, data_type: str, params: dict) -> AdapterResult:
        """Try each adapter in the chain. Return first success or final mock."""
        chain = self._fallback_chains.get(data_type, [])
        last_result = None

        for name in chain:
            adapter = self._adapters.get(name)
            if not adapter:
                logger.warning("adapter_not_found_in_chain", adapter=name, data_type=data_type)
                continue
            try:
                result = await adapter.fetch(params)
                if result.status in (SourceStatus.LIVE, SourceStatus.STALE):
                    logger.info(
                        "adapter_fetch_success",
                        adapter=name,
                        data_type=data_type,
                        status=result.status,
                    )
                    return result
                last_result = result
            except Exception as e:
                logger.error(
                    "adapter_fetch_error",
                    adapter=name,
                    data_type=data_type,
                    error=str(e),
                )
                last_result = AdapterResult(
                    data=None,
                    status=SourceStatus.DOWN,
                    source_name=name,
                    error_message=str(e),
                )

        # All adapters failed — return mock from primary
        primary = self._adapters.get(chain[0]) if chain else None
        if primary:
            logger.warning("all_adapters_failed_returning_mock", data_type=data_type)
            return primary.get_mock_data(params)

        return last_result or AdapterResult(
            data=None,
            status=SourceStatus.MOCK,
            source_name="unknown",
            error_message="No adapters configured for this data type",
        )

    async def health_all(self) -> dict[str, str]:
        """Probe every registered adapter and return status map."""
        results = {}
        for name, adapter in self._adapters.items():
            try:
                status = await adapter.health_check()
                results[name] = status.value
            except Exception:
                results[name] = SourceStatus.DOWN.value
        return results

    @property
    def adapter_names(self) -> list[str]:
        return list(self._adapters.keys())


# Global singleton
registry = AdapterRegistry()
