from typing import *
import logging

try:
    import coloredlogs
except ImportError:
    coloredlogs = None

l: logging.Logger = logging.getLogger(__name__)


# From https://stackoverflow.com/a/56810619/4334568
def reset_logging():
    manager = logging.root.manager
    manager.disabled = logging.NOTSET
    for logger in manager.loggerDict.values():
        if isinstance(logger, logging.Logger):
            logger.setLevel(logging.NOTSET)
            logger.propagate = True
            logger.disabled = False
            logger.filters.clear()
            handlers = logger.handlers.copy()
            for handler in handlers:
                # Copied from `logging.shutdown`.
                try:
                    handler.acquire()
                    handler.flush()
                    handler.close()
                except (OSError, ValueError):
                    pass
                finally:
                    handler.release()
                logger.removeHandler(handler)


def init_logging(logging_cfg: Dict[str, Any]):
    reset_logging()
    loggers_cfg = logging_cfg["Loggers"]
    for logger_name in loggers_cfg:
        if logger_name == "root":
            log: logging.Logger = logging.root
        else:
            log: logging.Logger = logging.getLogger(logger_name)
        log.setLevel(loggers_cfg[logger_name])

    stream_handler = logging.StreamHandler()
    if coloredlogs is not None:
        stream_handler.formatter = coloredlogs.ColoredFormatter(logging_cfg["log_format"], style="{")
    else:
        stream_handler.formatter = logging.Formatter(logging_cfg["log_format"], style="{")
    logging.root.handlers.clear()
    logging.root.addHandler(stream_handler)

    l.debug("Logging: ready")
