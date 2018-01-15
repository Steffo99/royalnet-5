import asyncio
import functools
import concurrent.futures

loop = asyncio.get_event_loop()
executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

async def call_me():
    await loop.run_in_executor(executor, functools.partial(print, "ciao"))
    return

async def spam_calls():
    while True:
        asyncio.ensure_future(call_me())
        await asyncio.sleep(1)

loop.run_until_complete(spam_calls())