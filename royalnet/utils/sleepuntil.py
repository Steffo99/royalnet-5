import asyncio
import datetime


async def sleep_until(dt: datetime.datetime) -> None:
    """Block the call until the specified datetime.

    Warning:
        Accurate only to seconds."""
    now = datetime.datetime.now()
    if now > dt:
        return
    delta = dt - now
    await asyncio.sleep(delta.total_seconds())
