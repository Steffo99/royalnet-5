import asyncio
import functools
import typing


async def asyncify(function: typing.Callable, *args, loop: typing.Optional[asyncio.AbstractEventLoop] = None, **kwargs):
    """Asyncronously run the function in a executor, allowing it to run asyncronously.

    Args:
        function: The function to call.
        args: The arguments to pass to the function.
        kwargs: The keyword arguments to pass to the function.
        loop: The loop to run the function in. If :const:`None`, run it in in the current event loop.

    Warning:
        The called function must be thread-safe!

    Warning:
        Calling a function this way might be significantly slower than calling its blocking counterpart!"""
    if not loop:
        loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, functools.partial(function, *args, **kwargs))
