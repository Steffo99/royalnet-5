import logging
import sys
import traceback
from typing import *
from royalnet.version import semantic
import functools

try:
    import sentry_sdk
    from sentry_sdk.integrations.aiohttp import AioHttpIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
except ImportError:
    sentry_sdk = None
    AioHttpIntegration = None
    SqlalchemyIntegration = None
    LoggingIntegration = None


log = logging.getLogger(__name__)


def init_sentry(sentry_cfg: Dict[str, Any]):
    if sentry_sdk is None:
        raise ImportError("`sentry` extra is not installed")
    log.debug("Initializing Sentry...")
    release = f"royalnet@{semantic}"
    sentry_sdk.init(sentry_cfg["dsn"],
                    integrations=[AioHttpIntegration(),
                                  SqlalchemyIntegration(),
                                  LoggingIntegration(event_level=None)],
                    release=release)
    log.info(f"Sentry: {release}")


# noinspection PyUnreachableCode
def sentry_exc(exc: Exception,
               level: str = "ERROR"):
    if sentry_sdk is not None:
        with sentry_sdk.configure_scope() as scope:
            scope.set_level(level.lower())
            sentry_sdk.capture_exception(exc)
    level_int: int = logging._nameToLevel[level.upper()]
    log.log(level_int, f"Captured {level.capitalize()}: {exc}")
    # If started in debug mode (without -O), raise the exception, allowing you to see its source
    if __debug__:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)


def sentry_wrap(level: str = "ERROR"):
    def decorator(func: Callable):
        @functools.wraps(func)
        def new_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                sentry_exc(exc=exc, level=level)
                raise
        return new_func
    return decorator


def sentry_async_wrap(level: str = "ERROR"):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def new_func(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                sentry_exc(exc=exc, level=level)
                raise
        return new_func
    return decorator
