from typing import *
import logging

try:
    import coloredlogs
except ImportError:
    coloredlogs = None

l: logging.Logger = logging.getLogger(__name__)


def init_logging(logging_cfg: Dict[str, Any]):
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
    if len(logging.root.handlers) < 1:
        logging.root.addHandler(stream_handler)

    l.debug("Logging: ready")
