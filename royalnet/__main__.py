import click
import typing
import importlib
import royalnet as r
import multiprocessing
import keyring
from logging import Formatter, StreamHandler, getLogger, Logger

try:
    import coloredlogs
except ImportError:
    coloredlogs = None


@click.command()
@click.option("--telegram/--no-telegram", default=None,
              help="Enable/disable the Telegram bot.")
@click.option("--discord/--no-discord", default=None,
              help="Enable/disable the Discord bot.")
@click.option("--constellation/--no-constellation", default=None,
              help="Enable/disable the Constellation web server.")
@click.option("--herald/--no-herald", default=None,
              help="Enable/disable the integrated Herald server."
                   " If turned off, Royalnet will try to connect to another server.")
@click.option("--remote-herald-address", type=str, default=None,
              help="If --no-herald is specified, connect to the Herald server at this URL instead.")
@click.option("-c", "--constellation-port", default=44445,
              help="The port on which the Constellation will serve webpages on.")
@click.option("-a", "--alchemy-url", type=str, default=None,
              help="The Alchemy database path.")
@click.option("-h", "--herald-port", type=int, default=44444,
              help="The port on which the Herald should be running.")
@click.option("-p", "--pack", type=str, multiple=True, default=tuple(),
              help="Import the pack with the specified name and use it in the Royalnet instance.")
@click.option("-s", "--secrets-name", type=str, default="__default__",
              help="The name in the keyring that the secrets are stored with.")
@click.option("-l", "--log-level", type=str, default="INFO",
              help="Select how much information you want to be printed on the console."
                   " Valid log levels are: FATAL/ERROR/WARNING/INFO/DEBUG")
def run(telegram: typing.Optional[bool],
        discord: typing.Optional[bool],
        constellation: typing.Optional[bool],
        herald: typing.Optional[bool],
        remote_herald_address: typing.Optional[str],
        constellation_port: int,
        alchemy_url: typing.Optional[str],
        herald_port: int,
        pack: typing.Tuple[str],
        secrets_name: str,
        log_level: str):
    # Initialize logging
    royalnet_log: Logger = getLogger("royalnet")
    royalnet_log.setLevel(log_level)
    stream_handler = StreamHandler()
    if coloredlogs is not None:
        stream_handler.formatter = coloredlogs.ColoredFormatter("{asctime}\t| {processName}\t| {name}\t| {message}",
                                                                style="{")
    else:
        stream_handler.formatter = Formatter("{asctime}\t| {processName}\t| {name}\t| {message}",
                                             style="{")
    royalnet_log.addHandler(stream_handler)
    royalnet_log.debug("Logging: ready")

    def get_secret(username: str):
        return keyring.get_password(f"Royalnet/{secrets_name}", username)

    # Enable / Disable interfaces
    interfaces = {
        "telegram": telegram,
        "discord": discord,
        "herald": herald,
        "constellation": constellation,
    }
    # If any interface is True, then the undefined ones should be False
    if any(interfaces[name] is True for name in interfaces):
        for name in interfaces:
            if interfaces[name] is None:
                interfaces[name] = False
    # Likewise, if any interface is False, then the undefined ones should be True
    elif any(interfaces[name] is False for name in interfaces):
        for name in interfaces:
            if interfaces[name] is None:
                interfaces[name] = True
    # Otherwise, if no interfaces are specified, all should be enabled
    else:
        assert all(interfaces[name] is None for name in interfaces)
        for name in interfaces:
            interfaces[name] = True

    herald_process: typing.Optional[multiprocessing.Process] = None
    # Start the Herald server
    if interfaces["herald"]:
        herald_config = r.herald.Config(name="<server>",
                                        address="127.0.0.1",
                                        port=herald_port,
                                        secret=get_secret("herald"),
                                        secure=False,
                                        path="/")
        herald_kwargs = {
            "log_level": log_level
        }
        herald_process = multiprocessing.Process(name="Herald Server",
                                                 target=r.herald.Server(config=herald_config).run_blocking,
                                                 kwargs=herald_kwargs,
                                                 daemon=True)
        herald_process.start()
    else:
        herald_config = r.herald.Config(name=...,
                                        address=remote_herald_address,
                                        port=herald_port,
                                        secret=get_secret("herald"),
                                        secure=False,
                                        path="/")

    # Import command and star packs
    packs: typing.List[str] = list(pack)
    packs.append("royalnet.backpack")  # backpack is always imported
    enabled_commands = []
    enabled_page_stars = []
    enabled_exception_stars = []
    enabled_events = []
    for pack in packs:
        imported = importlib.import_module(pack)
        try:
            imported_commands = imported.available_commands
        except AttributeError:
            raise click.ClickException(f"{pack} isn't a Royalnet Pack as it is missing available_commands.")
        try:
            imported_page_stars = imported.available_page_stars
        except AttributeError:
            raise click.ClickException(f"{pack} isn't a Royalnet Pack as it is missing available_page_stars.")
        try:
            imported_exception_stars = imported.available_exception_stars
        except AttributeError:
            raise click.ClickException(f"{pack} isn't a Royalnet Pack as it is missing available_exception_stars.")
        try:
            imported_events = imported.available_events
        except AttributeError:
            raise click.ClickException(f"{pack} isn't a Royalnet Pack as it is missing available_events.")
        enabled_commands = [*enabled_commands, *imported_commands]
        enabled_page_stars = [*enabled_page_stars, *imported_page_stars]
        enabled_exception_stars = [*enabled_exception_stars, *imported_exception_stars]
        enabled_events = [*enabled_events, *imported_events]

    telegram_process: typing.Optional[multiprocessing.Process] = None
    if interfaces["telegram"]:
        if alchemy_url is not None:
            telegram_db_config = r.serf.AlchemyConfig(database_url=alchemy_url,
                                                      master_table=r.backpack.tables.User,
                                                      identity_table=r.backpack.tables.Telegram,
                                                      identity_column="tg_id")
        else:
            telegram_db_config = None
        telegram_serf_kwargs = {
            'alchemy_config': telegram_db_config,
            'commands': enabled_commands,
            'events': enabled_events,
            'herald_config': herald_config.copy(name="telegram"),
            'secrets_name': secrets_name,
            'log_level': log_level,
        }
        telegram_process = multiprocessing.Process(name="Telegram Serf",
                                                   target=r.serf.telegram.TelegramSerf.run_process,
                                                   kwargs=telegram_serf_kwargs,
                                                   daemon=True)
        telegram_process.start()

    discord_process: typing.Optional[multiprocessing.Process] = None
    if interfaces["discord"]:
        if alchemy_url is not None:
            discord_db_config = r.serf.AlchemyConfig(database_url=alchemy_url,
                                                     master_table=r.backpack.tables.User,
                                                     identity_table=r.backpack.tables.Discord,
                                                     identity_column="discord_id")
        else:
            discord_db_config = None
        discord_serf_kwargs = {
            'alchemy_config': discord_db_config,
            'commands': enabled_commands,
            'events': enabled_events,
            'herald_config': herald_config.copy(name="discord"),
            'secrets_name': secrets_name,
            'log_level': log_level,
        }
        discord_process = multiprocessing.Process(name="Discord Serf",
                                                  target=r.serf.discord.DiscordSerf.run_process,
                                                  kwargs=discord_serf_kwargs,
                                                  daemon=True)
        discord_process.start()

    constellation_process: typing.Optional[multiprocessing.Process] = None
    if interfaces["constellation"]:
        # Create the Constellation
        constellation_kwargs = {
            'address': "127.0.0.1",
            'port': constellation_port,
            'secrets_name': secrets_name,
            'database_uri': alchemy_url,
            'page_stars': enabled_page_stars,
            'exc_stars': enabled_exception_stars,
            'log_level': log_level,
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
