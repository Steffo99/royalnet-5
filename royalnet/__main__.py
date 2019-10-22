import click
import typing
import importlib
import royalnet as r
import royalherald as rh
import multiprocessing
import keyring


@click.command()
@click.option("--telegram/--no-telegram", default=None,
              help="Enable/disable the Telegram module.")
@click.option("--discord/--no-discord", default=None,
              help="Enable/disable the Discord module.")
@click.option("-d", "--database", type=str, default=None,
              help="The PostgreSQL database path.")
@click.option("-p", "--packs", type=str, multiple=True, default=[],
              help="The names of the Packs that should be used.")
@click.option("-n", "--network-address", type=str, default=None,
              help="The Network server URL to connect to.")
@click.option("-l", "--local-network-server", is_flag=True, default=False,
              help="Locally run a Network server and bind it to port 44444. Overrides -n.")
@click.option("-s", "--secrets-name", type=str, default="__default__",
              help="The name in the keyring that the secrets are stored with.")
@click.option("-v", "--verbose", is_flag=True, default=False,
              help="Print all possible debug information.")
def run(telegram: typing.Optional[bool],
        discord: typing.Optional[bool],
        database: typing.Optional[str],
        packs: typing.Tuple[str],
        network_address: typing.Optional[str],
        local_network_server: bool,
        secrets_name: str,
        verbose: bool):

    # Get the network password
    network_password = keyring.get_password(f"Royalnet/{secrets_name}", "network")

    # Get the sentry dsn
    sentry_dsn = keyring.get_password(f"Royalnet/{secrets_name}", "sentry")

    # Enable / Disable interfaces
    interfaces = {
        "telegram": telegram,
        "discord": discord
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
                                                 target=rh.Server("0.0.0.0", 44444, network_password).run_blocking,
                                                 daemon=True)
        server_process.start()
        network_address = "ws://127.0.0.1:44444/"

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

    # Import command packs
    packs: typing.List[str] = list(packs)
    packs.append("royalnet.packs.common")  # common pack is always imported
    enabled_commands = []
    for pack in packs:
        imported = importlib.import_module(pack)
        try:
            imported_commands = imported.available_commands
        except AttributeError:
            raise click.ClickException(f"{pack} isn't a Royalnet Pack.")
        enabled_commands = [*enabled_commands, *imported_commands]

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

    click.echo("Royalnet processes have been started. You can force-quit by pressing Ctrl+C.")
    if server_process is not None:
        server_process.join()
    if telegram_process is not None:
        telegram_process.join()
    if discord_process is not None:
        discord_process.join()


if __name__ == "__main__":
    run()
