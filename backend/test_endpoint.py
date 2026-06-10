import asyncio
import traceback
from app.api.v1.router import get_spare_capacity

async def test():
    try:
        res = await get_spare_capacity()
        print(res)
    except Exception as e:
        traceback.print_exc()

asyncio.run(test())
