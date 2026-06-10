"""EIA API v2 adapter — energy production, consumption, storage, petroleum data."""

import httpx
import structlog
from datetime import datetime
from app.adapters.base import DataAdapter, AdapterResult, SourceStatus
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# EIA API v2 series IDs for key fundamentals
EIA_SERIES = {
    "us_crude_stocks": "PET.WCESTUS1.W",
    "cushing_inventory": "PET.W_EPC0_SAX_YCUOK_MBBL.W",
    "us_production": "PET.WCRFPUS2.W",
    "refinery_utilization": "PET.WPULEUS3.W",
    "us_imports": "PET.WCRIMUS2.W",
    "us_exports": "PET.WCREXUS2.W",
    "spr_level": "PET.WCSSTUS1.W",
    "rig_count": "PET.E_ERTRRO_XR0_NUS_C.W",
    "steo_supply": "STEO.PAPR_WORLD.M",
    "steo_demand": "STEO.PATC_WORLD.M",
    "steo_opec": "STEO.PAPR_OPEC.M",
    "steo_non_opec": "STEO.PAPR_NON_OPEC.M",
}


class EIAAdapter(DataAdapter):
    """EIA API v2 for energy fundamentals."""

    BASE_URL = "https://api.eia.gov/v2"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    @property
    def source_name(self) -> str:
        return "eia"

    async def fetch(self, params: dict) -> AdapterResult:
        data_type = params.get("type", "fundamentals")

        try:
            if data_type == "fundamentals":
                return await self._fetch_fundamentals(params)
            elif data_type == "steo":
                return await self._fetch_steo(params)
            elif data_type == "series":
                return await self._fetch_series(params)
            else:
                return self.get_mock_data(params)
        except Exception as e:
            logger.error("eia_fetch_error", error=str(e), data_type=data_type)
            return AdapterResult(
                data=None, status=SourceStatus.DOWN,
                source_name=self.source_name, error_message=str(e),
            )

    async def _fetch_series(self, params: dict) -> AdapterResult:
        series_id = params.get("series_id")
        if not series_id:
            return self.get_mock_data(params)

        resp = await self.client.get(
            f"{self.BASE_URL}/seriesid/{series_id}",
            params={"api_key": settings.eia_api_key, "num": params.get("num", 52)},
        )
        resp.raise_for_status()
        data = resp.json()

        if "response" in data and "data" in data["response"]:
            return AdapterResult(
                data=data["response"]["data"],
                status=SourceStatus.LIVE,
                source_name=self.source_name,
            )

        return self.get_mock_data(params)

    async def _fetch_fundamentals(self, params: dict) -> AdapterResult:
        """Fetch key fundamental indicators from EIA."""
        results = {}
        for key, series_id in EIA_SERIES.items():
            if key.startswith("steo_"):
                continue
            try:
                resp = await self.client.get(
                    f"{self.BASE_URL}/seriesid/{series_id}",
                    params={"api_key": settings.eia_api_key, "num": 10},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if "response" in data and "data" in data["response"]:
                        series_data = data["response"]["data"]
                        if series_data:
                            latest = series_data[0]
                            prior = series_data[1] if len(series_data) > 1 else series_data[0]
                            results[key] = {
                                "value": latest.get("value"),
                                "date": latest.get("period"),
                                "prior_value": prior.get("value"),
                            }
            except Exception as e:
                logger.warning("eia_series_error", series=key, error=str(e))

        if not results:
            return self.get_mock_data(params)

        return AdapterResult(
            data=results, status=SourceStatus.LIVE, source_name=self.source_name,
        )

    async def _fetch_steo(self, params: dict) -> AdapterResult:
        """Fetch STEO supply/demand projections."""
        steo_data = []
        for key in ["steo_supply", "steo_demand", "steo_opec", "steo_non_opec"]:
            series_id = EIA_SERIES.get(key)
            if not series_id:
                continue
            try:
                resp = await self.client.get(
                    f"{self.BASE_URL}/seriesid/{series_id}",
                    params={"api_key": settings.eia_api_key, "num": 12},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if "response" in data and "data" in data["response"]:
                        steo_data.append({
                            "series": key.replace("steo_", ""),
                            "data": data["response"]["data"],
                        })
            except Exception as e:
                logger.warning("eia_steo_error", series=key, error=str(e))

        if not steo_data:
            return self.get_mock_data(params)

        return AdapterResult(
            data=steo_data, status=SourceStatus.LIVE, source_name=self.source_name,
        )

    async def health_check(self) -> SourceStatus:
        try:
            resp = await self.client.get(
                f"{self.BASE_URL}/seriesid/PET.RWTC.D",
                params={"api_key": settings.eia_api_key, "num": 1},
            )
            return SourceStatus.LIVE if resp.status_code == 200 else SourceStatus.DOWN
        except Exception:
            return SourceStatus.DOWN

    def get_mock_data(self, params: dict) -> AdapterResult:
        data_type = params.get("type", "fundamentals")
        if data_type == "fundamentals":
            return AdapterResult(
                data={
                    "us_crude_stocks": {"value": 457.2, "date": "2026-05-30", "prior_value": 463.3},
                    "cushing_inventory": {"value": 34.6, "date": "2026-05-30", "prior_value": 35.2},
                    "us_production": {"value": 13.4, "date": "2026-05-30", "prior_value": 13.3},
                    "refinery_utilization": {"value": 93.2, "date": "2026-05-30", "prior_value": 92.4},
                    "spr_level": {"value": 372.4, "date": "2026-05-30", "prior_value": 371.6},
                    "rig_count": {"value": 584, "date": "2026-05-30", "prior_value": 587},
                },
                status=SourceStatus.MOCK,
                source_name=self.source_name,
                error_message="EIA API unavailable — returning mock data",
            )
        return super().get_mock_data(params)
