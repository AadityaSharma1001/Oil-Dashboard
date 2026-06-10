"""Shipping adapter — live tankermap integration for chokepoints, floating storage, China flows."""

import httpx
import structlog
from datetime import datetime, timezone
from app.adapters.base import DataAdapter, AdapterResult, SourceStatus
from app.analytics.shipping import (
    detect_floating_storage,
    analyze_chokepoint_traffic,
    analyze_china_imports,
    compute_fleet_summary,
)

logger = structlog.get_logger()


class ShippingAdapter(DataAdapter):
    """
    Shipping/tanker analytics adapter.
    Uses TankerMap API for live vessel tracking and processes data using
    the shipping analytics engine to identify floating storage, chokepoint transit,
    and import flows.
    """

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=20.0)

    @property
    def source_name(self) -> str:
        return "shipping"

    async def fetch(self, params: dict) -> AdapterResult:
        data_type = params.get("type", "chokepoints")

        try:
            # Fetch live vessel data
            response = await self.client.get(
                "https://tankermap.com/api/vessels/live?fields=map",
                headers={"User-Agent": "OilDesk/1.0"}
            )
            response.raise_for_status()
            vessels = response.json()

            if not vessels or not isinstance(vessels, list):
                raise ValueError("Invalid format from TankerMap")

            logger.info("shipping_fetch_success", vessel_count=len(vessels))

            if data_type == "chokepoints":
                chokepoint_data = analyze_chokepoint_traffic(vessels)
                return AdapterResult(
                    data=chokepoint_data,
                    status=SourceStatus.LIVE,
                    source_name=self.source_name,
                    fetched_at=datetime.now(timezone.utc)
                )

            elif data_type == "floating_storage":
                fs_data = detect_floating_storage(vessels)
                return AdapterResult(
                    data=fs_data,
                    status=SourceStatus.LIVE,
                    source_name=self.source_name,
                    fetched_at=datetime.now(timezone.utc)
                )

            elif data_type == "china_imports":
                china_data = analyze_china_imports(vessels)
                return AdapterResult(
                    data=china_data,
                    status=SourceStatus.LIVE,
                    source_name=self.source_name,
                    fetched_at=datetime.now(timezone.utc)
                )

            elif data_type == "fleet_utilization":
                fleet_data = compute_fleet_summary(vessels)
                return AdapterResult(
                    data=fleet_data,
                    status=SourceStatus.LIVE,
                    source_name=self.source_name,
                    fetched_at=datetime.now(timezone.utc)
                )

            elif data_type == "vlcc_rates":
                return self._vlcc_rates_data()

            else:
                return self.get_mock_data(params)

        except Exception as e:
            logger.error("shipping_fetch_error", error=str(e), data_type=data_type)
            # Fall back to structured mock data
            if data_type == "chokepoints":
                return self._chokepoint_data()
            elif data_type == "floating_storage":
                return self._floating_storage_data()
            elif data_type == "vlcc_rates":
                return self._vlcc_rates_data()
            elif data_type == "fleet_utilization":
                return self._fleet_data()
            else:
                return self.get_mock_data(params)

    def _chokepoint_data(self) -> AdapterResult:
        """Mock fallback for chokepoints."""
        return AdapterResult(
            data={
                "strait_of_hormuz": {
                    "label": "Strait of Hormuz", "total_vessels": 45, "oil_transiting": 14,
                    "transit_estimated_bbl": 21000000,
                },
                "strait_of_malacca": {
                    "label": "Strait of Malacca", "total_vessels": 250, "oil_transiting": 88,
                    "transit_estimated_bbl": 16500000,
                },
            },
            status=SourceStatus.MOCK, source_name=self.source_name,
        )

    def _floating_storage_data(self) -> AdapterResult:
        """Mock fallback for floating storage."""
        return AdapterResult(
            data={
                "total_vessels": 210,
                "total_estimated_mb": 214.5,
                "by_region": {
                    "Middle East Gulf": {"vessels": [1]*45, "bbl": 50200000},
                    "Southeast Asia": {"vessels": [1]*75, "bbl": 85000000},
                    "West Africa": {"vessels": [1]*20, "bbl": 22000000},
                },
            },
            status=SourceStatus.MOCK, source_name=self.source_name,
        )

    def _vlcc_rates_data(self) -> AdapterResult:
        """Mock data for VLCC rates (no live free API for this)."""
        return AdapterResult(
            data=[
                {"route": "MEG-Japan", "worldscale_rate": 52.5, "tce_usd_per_day": 28500},
                {"route": "MEG-China", "worldscale_rate": 55.0, "tce_usd_per_day": 31200},
                {"route": "WAF-China", "worldscale_rate": 58.2, "tce_usd_per_day": 34800},
                {"route": "USG-NWE", "worldscale_rate": 48.0, "tce_usd_per_day": 25100},
            ],
            status=SourceStatus.MOCK, source_name=self.source_name,
        )

    def _fleet_data(self) -> AdapterResult:
        """Mock fallback for fleet utilization."""
        return AdapterResult(
            data={
                "total_vessels": 4900,
                "oil_tankers": 4050,
                "lng_tankers": 850,
            },
            status=SourceStatus.MOCK, source_name=self.source_name,
        )

    async def health_check(self) -> SourceStatus:
        try:
            r = await self.client.get("https://tankermap.com/api/vessels/live?fields=map")
            if r.status_code == 200:
                return SourceStatus.LIVE
        except Exception:
            pass
        return SourceStatus.MOCK
