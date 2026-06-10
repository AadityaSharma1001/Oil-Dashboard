import asyncio
import httpx
from app.config import get_settings

async def main():
    s = get_settings()
    async with httpx.AsyncClient() as c:
        # Check current Cushing series
        r1 = await c.get('https://api.eia.gov/v2/seriesid/PET.WCRSTOK1.W', params={'api_key': s.eia_api_key, 'num': 2})
        print("PET.WCRSTOK1.W:", r1.status_code, r1.text[:200])

        # Check the correct Cushing series
        r2 = await c.get('https://api.eia.gov/v2/seriesid/PET.W_EPC0_SAX_YCUOK_MBBL.W', params={'api_key': s.eia_api_key, 'num': 2})
        print("PET.W_EPC0_SAX_YCUOK_MBBL.W:", r2.status_code, r2.text[:200])

if __name__ == "__main__":
    asyncio.run(main())
