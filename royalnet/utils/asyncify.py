import asyncio
import functools
import typing


async def asyncify(function: typing.Callable, *args, loop: typing.Optional[asyncio.AbstractEventLoop] = None, **kwargs):
    """Asyncronously run the function in a different thread or process, preventing it from blocking the event loop.

    Warning:
        If the function has side effects, it may behave strangely."""
    if not loop:
        loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, functools.partial(function, *args, **kwargs))
