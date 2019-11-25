import click
import typing
import importlib
import royalnet as r
import multiprocessing
import toml
from logging import Formatter, StreamHandler, getLogger, Logger

try:
    import coloredlogs
except ImportError:
    coloredlogs = None


log = getLogger(__name__)


@click.command()
@click.option("-c", "--config-filename", default="./config.toml", type=str,
              help="The filename of the Royalnet configuration file.")
def run(config_filename: str):
    # Read the configuration file
    with open(config_filename, "r") as t:
        config: dict = toml.load(t)

    # Initialize logging
    royalnet_log: Logger = getLogger("royalnet")
    royalnet_log.setLevel(config["Logging"]["log_level"])
    stream_handler = StreamHandler()
    if coloredlogs is not None:
        stream_handler.formatter = coloredlogs.ColoredFormatter("{asctime}\t| {processName}\t| {name}\t| {message}",
                                                                style="{")
    else:
        stream_handler.formatter = Formatter("{asctime}\t| {processName}\t| {name}\t| {message}",
                                             style="{")
    royalnet_log.addHandler(stream_handler)
    log.info("Logging: ready")

    ...


if __name__ == "__main__":
    run()
