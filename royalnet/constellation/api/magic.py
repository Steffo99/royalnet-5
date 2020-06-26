from typing import *
import functools


def magic(func):
    # i made this at 2:00 am
    # at 2:15 am i already had no idea on how it worked
    # at 2:30 i still have no idea but it works appearently
    # 2:40 TODO: document me
    func.__magic__ = True

    @functools.wraps(func)
    async def f(*args, **kwargs):
        return await func(*args, **kwargs)
    return f
