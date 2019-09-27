import click
import typing
import royalnet as r


@click.command()
@click.option("--telegram/--no-telegram", default=None,
              help="Enable/disable the Telegram module.")
@click.option("--discord/--no-discord", default=None,
              help="Enable/disable the Discord module.")
@click.option("--database", type=str, default=None,
              help="The PostgreSQL database path.")
@click.option("--commands", type=str, multiple=True, default=[],
              help="The names of the command pack modules that should be imported.")
@click.option("--network", type=str, default=None,
              help="The Royalnet master server uri and password, separated by a pipe.")
def run(telegram: typing.Optional[bool],
        discord: typing.Optional[bool],
        database: typing.Optional[str],
        commands: typing.List[str],
        network: typing.Optional[str]):
    ...


if __name__ == "__main__":
    run()
