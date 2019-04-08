import asyncio
import datetime


async def sleep_until(dt: datetime.datetime):
    now = datetime.datetime.now()
    if now > dt:
        return
    delta = dt - now
    await asyncio.sleep(delta.total_seconds())
