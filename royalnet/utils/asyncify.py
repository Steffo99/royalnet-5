import asyncio
import functools
import typing


async def asyncify(function: typing.Callable, *args, **kwargs):
    # TODO: make cancellable somehow
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, functools.partial(function, *args, **kwargs))
