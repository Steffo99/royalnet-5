import functools


def magic(func):
    """Mark a function as "magic", so its override can be detected externally."""
    func.__magic__ = True

    @functools.wraps(func)
    async def f(*args, **kwargs):
        return await func(*args, **kwargs)

    return f
