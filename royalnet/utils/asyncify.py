import asyncio
import functools
import typing


async def asyncify(function: typing.Callable, *args, **kwargs):
    """Convert a function into a coroutine.

    Warning:
        The coroutine cannot be cancelled, and any attempts to do so will result in unexpected outputs."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, functools.partial(function, *args, **kwargs))
