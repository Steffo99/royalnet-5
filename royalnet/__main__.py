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
    royalnet_log.info("Logging: ready")

    herald_process: typing.Optional[multiprocessing.Process] = None
    herald_config = r.herald.Config(name="<server>",
                                    address=config["Herald"]["Local"]["address"],
                                    port=config["Herald"]["Local"]["port"],
                                    secret=config["Herald"]["Local"]["secret"],
                                    secure=config["Herald"]["Local"]["secure"],
                                    path=config["Herald"]["Local"]["path"])
    # Start the Herald server
    if config["Herald"]["Local"]["enabled"]:
        herald_process = multiprocessing.Process(name="Herald Server",
                                                 target=r.herald.Server(config=herald_config).run_blocking,
                                                 daemon=True)
        herald_process.start()
    elif config["Herald"]["Remote"]["enabled"]:
        # Other processes will connect to the remote Herald independently
        pass
    else:
        royalnet_log.fatal("No Heralds are enabled, Royalnet can't function!")
        exit(1)

    # Import command and star packs
    packs: typing.List[str] = config["Packs"]["active"]
    enabled_commands = []
    enabled_page_stars = []
    enabled_exception_stars = []
    enabled_events = []
    for pack in packs:
        imported = importlib.import_module(pack)
        try:
            imported_commands = imported.available_commands
        except AttributeError:
            royalnet_log.error(f"{pack} isn't a Royalnet Pack as it is missing available_commands.")
            continue
        try:
            imported_page_stars = imported.available_page_stars
        except AttributeError:
            royalnet_log.error(f"{pack} isn't a Royalnet Pack as it is missing available_page_stars.")
            continue
        try:
            imported_exception_stars = imported.available_exception_stars
        except AttributeError:
            royalnet_log.error(f"{pack} isn't a Royalnet Pack as it is missing available_exception_stars.")
            continue
        try:
            imported_events = imported.available_events
        except AttributeError:
            royalnet_log.error(f"{pack} isn't a Royalnet Pack as it is missing available_events.")
            continue
        enabled_commands = [*enabled_commands, *imported_commands]
        enabled_page_stars = [*enabled_page_stars, *imported_page_stars]
        enabled_exception_stars = [*enabled_exception_stars, *imported_exception_stars]
        enabled_events = [*enabled_events, *imported_events]

    telegram_process: typing.Optional[multiprocessing.Process] = None
    if config["Serf"]["Telegram"]["enabled"]:
        if config["Alchemy"]["enabled"] is not None:
            telegram_db_config = r.serf.AlchemyConfig(database_url=config["Alchemy"]["database_url"],
                                                      master_table=r.backpack.tables.User,
                                                      identity_table=r.backpack.tables.Telegram,
                                                      identity_column="tg_id")
        else:
            telegram_db_config = None
        telegram_serf_kwargs = {
            'token': config["Serf"]["Telegram"]["token"],
            'alchemy_config': telegram_db_config,
            'commands': enabled_commands,
            'events': enabled_events,
            'herald_config': herald_config.copy(name="telegram"),
            'log_level': config["Logging"]["log_level"],
            'sentry_dsn': config["Sentry"]["dsn"],
        }
        telegram_process = multiprocessing.Process(name="Telegram Serf",
                                                   target=r.serf.telegram.TelegramSerf.run_process,
                                                   kwargs=telegram_serf_kwargs,
                                                   daemon=True)
        telegram_process.start()

    discord_process: typing.Optional[multiprocessing.Process] = None
    if config["Serf"]["Discord"]["enabled"]:
        if config["Alchemy"]["enabled"] is not None:
            discord_db_config = r.serf.AlchemyConfig(database_url=config["Alchemy"]["database_url"],
                                                     master_table=r.backpack.tables.User,
                                                     identity_table=r.backpack.tables.Discord,
                                                     identity_column="discord_id")
        else:
            discord_db_config = None
        discord_serf_kwargs = {
            'token': config["Serf"]["Discord"]["token"],
            'alchemy_config': discord_db_config,
            'commands': enabled_commands,
            'events': enabled_events,
            'herald_config': herald_config.copy(name="discord"),
            'log_level': config["Logging"]["log_level"],
            'sentry_dsn': config["Sentry"]["dsn"],
        }
        discord_process = multiprocessing.Process(name="Discord Serf",
                                                  target=r.serf.discord.DiscordSerf.run_process,
                                                  kwargs=discord_serf_kwargs,
                                                  daemon=True)
        discord_process.start()

    constellation_process: typing.Optional[multiprocessing.Process] = None
    if config["Constellation"]["enabled"]:
        # Create the Constellation
        constellation_kwargs = {
            'address': config["Constellation"]["address"],
            'port': config["Constellation"]["port"],
            'database_uri': config["Alchemy"]["database_url"] if config["Alchemy"]["enabled"] else None,
            'page_stars': enabled_page_stars,
            'exc_stars': enabled_exception_stars,
            'log_level': config["Logging"]["log_level"],
        }
        constellation_process = multiprocessing.Process(name="Constellation",
                                                        target=r.constellation.Constellation.run_process,
                                                        kwargs=constellation_kwargs,
                                                        daemon=True)
        constellation_process.start()

    royalnet_log.info("Royalnet is now running!")
    if herald_process is not None:
        herald_process.join()
    if telegram_process is not None:
        telegram_process.join()
    if discord_process is not None:
        discord_process.join()
    if constellation_process is not None:
        constellation_process.join()


if __name__ == "__main__":
    run()
