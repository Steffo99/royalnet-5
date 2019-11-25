from typing import *
import logging

try:
    import coloredlogs
except ImportError:
    coloredlogs = None


log_format = "{asctime}\t| {processName}\t| {name}\t| {message}"


def init_logging(logging_cfg: Dict[str, Any]):
    royalnet_log: logging.Logger = logging.getLogger("royalnet")
    royalnet_log.setLevel(logging_cfg["log_level"])
    stream_handler = logging.StreamHandler()
    if coloredlogs is not None:
        stream_handler.formatter = coloredlogs.ColoredFormatter(log_format, style="{")
    else:
        stream_handler.formatter = logging.Formatter(log_format, style="{")
    if len(royalnet_log.handlers) < 1:
        royalnet_log.addHandler(stream_handler)
    royalnet_log.debug("Logging: ready")
