import click
import typing
import importlib
import royalnet as r
import royalherald as rh
import multiprocessing
import keyring
import logging


@click.command()
@click.option("--telegram/--no-telegram", default=None,
              help="Enable/disable the Telegram bot.")
@click.option("--discord/--no-discord", default=None,
              help="Enable/disable the Discord bot.")
@click.option("--webserver/--no-webserver", default=None,
              help="Enable/disable the Web server.")
@click.option("--webserver-port", default=8001,
              help="The port on which the web server will listen on.")
@click.option("-d", "--database", type=str, default=None,
              help="The PostgreSQL database path.")
@click.option("-p", "--packs", type=str, multiple=True, default=[],
              help="The names of the Packs that should be used.")
@click.option("-n", "--network-address", type=str, default=None,
              help="The Network server URL to connect to.")
@click.option("-l", "--local-network-server", is_flag=True, default=False,
              help="Locally run a Network server and bind it to port 44444. Overrides -n.")
@click.option("--local-network-server-port", type=int, default=44444,
              help="The port on which the local network will be ran.")
@click.option("-s", "--secrets-name", type=str, default="__default__",
              help="The name in the keyring that the secrets are stored with.")
@click.option("-v", "--verbose", is_flag=True, default=False,
              help="Print all possible debug information.")
def run(telegram: typing.Optional[bool],
        discord: typing.Optional[bool],
        webserver: typing.Optional[bool],
        webserver_port: typing.Optional[int],
        database: typing.Optional[str],
        packs: typing.Tuple[str],
        network_address: typing.Optional[str],
        local_network_server: bool,
        local_network_server_port: int,
        secrets_name: str,
        verbose: bool):
    # Setup logging
    if verbose:
        core_logger = logging.root
        core_logger.setLevel(logging.DEBUG)
        stream_handler = logging.StreamHandler()
        stream_handler.formatter = logging.Formatter("{asctime}\t{name}\t{levelname}\t{message}", style="{")
        core_logger.addHandler(stream_handler)
        core_logger.debug("Logging setup complete.")

    # Get the network password
    network_password = keyring.get_password(f"Royalnet/{secrets_name}", "network")

    # Get the sentry dsn
    sentry_dsn = keyring.get_password(f"Royalnet/{secrets_name}", "sentry")

    # Enable / Disable interfaces
    interfaces = {
        "telegram": telegram,
        "discord": discord,
        "webserver": webserver
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

    server_process: typing.Optional[multiprocessing.Process] = None
    # Start the network server
    if local_network_server:
        server_process = multiprocessing.Process(name="Network Server",
                                                 target=rh.Server("0.0.0.0", local_network_server_port, network_password).run_blocking,
                                                 daemon=True)
        server_process.start()
        network_address = f"ws://127.0.0.1:{local_network_server_port}/"

    # Create a Royalnet configuration
    network_config: typing.Optional[rh.Config] = None
    if network_address is not None:
        network_config = rh.Config(network_address, network_password)

    # Create a Alchemy configuration
    telegram_db_config: typing.Optional[r.database.DatabaseConfig] = None
    discord_db_config: typing.Optional[r.database.DatabaseConfig] = None
    if database is not None:
        telegram_db_config = r.database.DatabaseConfig(database,
                                                       r.packs.common.tables.User,
                                                       r.packs.common.tables.Telegram,
                                                       "tg_id")
        discord_db_config = r.database.DatabaseConfig(database,
                                                      r.packs.common.tables.User,
                                                      r.packs.common.tables.Discord,
                                                      "discord_id")

    # Import command and star packs
    packs: typing.List[str] = list(packs)
    packs.append("royalnet.packs.common")  # common pack is always imported
    enabled_commands = []
    enabled_page_stars = []
    enabled_exception_stars = []
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
        enabled_commands = [*enabled_commands, *imported_commands]
        enabled_page_stars = [*enabled_page_stars, *imported_page_stars]
        enabled_exception_stars = [*enabled_exception_stars, *imported_exception_stars]

    telegram_process: typing.Optional[multiprocessing.Process] = None
    if interfaces["telegram"]:
        click.echo("\n@BotFather Commands String")
        for command in enabled_commands:
            click.echo(f"{command.name} - {command.description}")
        click.echo("")
        telegram_bot = r.bots.TelegramBot(network_config=network_config,
                                          database_config=telegram_db_config,
                                          sentry_dsn=sentry_dsn,
                                          commands=enabled_commands,
                                          secrets_name=secrets_name)
        telegram_process = multiprocessing.Process(name="Telegram Interface",
                                                   target=telegram_bot.run_blocking,
                                                   args=(verbose,),
                                                   daemon=True)
        telegram_process.start()

    discord_process: typing.Optional[multiprocessing.Process] = None
    if interfaces["discord"]:
        discord_bot = r.bots.DiscordBot(network_config=network_config,
                                        database_config=discord_db_config,
                                        sentry_dsn=sentry_dsn,
                                        commands=enabled_commands,
                                        secrets_name=secrets_name)
        discord_process = multiprocessing.Process(name="Discord Interface",
                                                  target=discord_bot.run_blocking,
                                                  args=(verbose,),
                                                  daemon=True)
        discord_process.start()

    webserver_process: typing.Optional[multiprocessing.Process] = None
    if interfaces["webserver"]:
        # Common tables are always included
        constellation_tables = set(r.packs.common.available_tables)
        # Find the required tables
        for star in [*enabled_page_stars, *enabled_exception_stars]:
            constellation_tables = constellation_tables.union(star.tables)
        # Create the Constellation
        constellation = r.web.Constellation(page_stars=enabled_page_stars,
                                            exc_stars=enabled_exception_stars,
                                            secrets_name=secrets_name,
                                            database_uri=database,
                                            tables=constellation_tables)
        webserver_process = multiprocessing.Process(name="Constellation Webserver",
                                                    target=constellation.run_blocking,
                                                    args=("0.0.0.0", webserver_port, verbose,),
                                                    daemon=True)
        webserver_process.start()

    click.echo("Royalnet processes have been started. You can force-quit by pressing Ctrl+C.")
    if server_process is not None:
        server_process.join()
    if telegram_process is not None:
        telegram_process.join()
    if discord_process is not None:
        discord_process.join()
    if webserver_process is not None:
        webserver_process.join()


if __name__ == "__main__":
    run()
