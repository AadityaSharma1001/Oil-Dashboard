"""NHC adapter — NOAA National Hurricane Center active storms."""

import httpx
import structlog
from app.adapters.base import DataAdapter, AdapterResult, SourceStatus

logger = structlog.get_logger()

NHC_CURRENT_STORMS_URL = "https://www.nhc.noaa.gov/CurrentSurges.json"
NHC_ACTIVE_URL = "https://www.nhc.noaa.gov/CurrentStorms.json"


class NHCAdapter(DataAdapter):
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0, follow_redirects=True)

    @property
    def source_name(self) -> str:
        return "nhc"

    async def fetch(self, params: dict) -> AdapterResult:
        try:
            resp = await self.client.get(NHC_ACTIVE_URL)
            resp.raise_for_status()
            data = resp.json()

            storms = data.get("activeStorms", [])
            parsed = []
            for storm in storms:
                parsed.append({
                    "id": storm.get("id", ""),
                    "name": storm.get("name", "Unknown"),
                    "classification": storm.get("classification", ""),
                    "intensity": storm.get("intensity", 0),
                    "pressure": storm.get("pressure", 0),
                    "lat": storm.get("lat", 0),
                    "lon": storm.get("lon", 0),
                    "movement_dir": storm.get("movementDir", ""),
                    "movement_speed": storm.get("movementSpeed", 0),
                    "url": storm.get("url", ""),
                })

            return AdapterResult(
                data={"storms": parsed, "count": len(parsed)},
                status=SourceStatus.LIVE,
                source_name=self.source_name,
            )
        except Exception as e:
            logger.error("nhc_fetch_error", error=str(e))
            return self.get_mock_data(params)

    async def health_check(self) -> SourceStatus:
        try:
            resp = await self.client.get(NHC_ACTIVE_URL)
            return SourceStatus.LIVE if resp.status_code == 200 else SourceStatus.DOWN
        except Exception:
            return SourceStatus.DOWN

    def get_mock_data(self, params: dict) -> AdapterResult:
        return AdapterResult(
            data={
                "storms": [
                    {
                        "id": "AL042026", "name": "Hurricane Danielle",
                        "classification": "HU", "intensity": 105, "pressure": 968,
                        "lat": 25.4, "lon": -89.2,
                        "movement_dir": "NW", "movement_speed": 12,
                    },
                ],
                "count": 1,
            },
            status=SourceStatus.MOCK, source_name=self.source_name,
            error_message="NHC feed unavailable — returning mock data",
        )
