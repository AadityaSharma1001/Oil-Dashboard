"""CFTC COT adapter — Commitments of Traders data."""

import httpx
import structlog
from app.adapters.base import DataAdapter, AdapterResult, SourceStatus

logger = structlog.get_logger()

CFTC_URL = "https://publicreporting.cftc.gov/resource/kh3c-gbw2.json"

class CFTCAdapter(DataAdapter):
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=20.0)

    @property
    def source_name(self) -> str:
        return "cftc"

    async def fetch(self, params: dict) -> AdapterResult:
        try:
            commodity = params.get("commodity", "CRUDE OIL, LIGHT SWEET")
            weeks = params.get("weeks", 12)
            resp = await self.client.get(CFTC_URL, params={
                "$where": f"cftc_contract_market_code='067651'",
                "$order": "report_date_as_yyyy_mm_dd DESC",
                "$limit": weeks,
            })
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    parsed = []
                    for row in data:
                        parsed.append({
                            "report_date": row.get("report_date_as_yyyy_mm_dd"),
                            "managed_money_long": int(row.get("m_money_positions_long_all", 0)),
                            "managed_money_short": int(row.get("m_money_positions_short_all", 0)),
                            "producer_long": int(row.get("prod_merc_positions_long", 0)),
                            "producer_short": int(row.get("prod_merc_positions_short", 0)),
                            "swap_dealer_long": int(row.get("swap_positions_long_all", 0)),
                            "swap_dealer_short": int(row.get("swap__positions_short_all", 0)),
                        })
                    return AdapterResult(data=parsed, status=SourceStatus.LIVE, source_name=self.source_name)
            return self.get_mock_data(params)
        except Exception as e:
            logger.error("cftc_fetch_error", error=str(e))
            return self.get_mock_data(params)

    async def health_check(self) -> SourceStatus:
        try:
            resp = await self.client.get(CFTC_URL, params={"$limit": 1})
            return SourceStatus.LIVE if resp.status_code == 200 else SourceStatus.DOWN
        except Exception:
            return SourceStatus.DOWN

    def get_mock_data(self, params: dict) -> AdapterResult:
        mm_net = [185, 192, 178, 165, 172, 180, 195, 210, 225, 218, 230, 242]
        prod_net = [-220, -215, -210, -205, -218, -225, -240, -255, -268, -260, -275, -285]
        swap_net = [-45, -48, -42, -38, -40, -44, -50, -55, -60, -58, -62, -65]
        data = []
        for i in range(12):
            data.append({
                "report_date": f"W-{12 - i}",
                "managed_money_long": mm_net[i] * 1000, "managed_money_short": 0,
                "producer_long": 0, "producer_short": abs(prod_net[i]) * 1000,
                "swap_dealer_long": 0, "swap_dealer_short": abs(swap_net[i]) * 1000,
            })
        return AdapterResult(data=data, status=SourceStatus.MOCK, source_name=self.source_name, error_message="CFTC unavailable — returning mock COT data")
