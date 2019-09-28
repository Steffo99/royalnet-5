import click
import keyring


@click.command()
def run():
    click.echo("Welcome to the Royalnet configuration creator!")
    secrets_name = click.prompt("Desired secrets name", default="__default__")
    network = click.prompt("Network password", default="")
    if network:
        keyring.set_password(f"Royalnet/{secrets_name}", "network", network)
    telegram = click.prompt("Telegram Bot API token", default="")
    if telegram:
        keyring.set_password(f"Royalnet/{secrets_name}", "telegram", telegram)
    discord = click.prompt("Discord Bot API token", default="")
    if discord:
        keyring.set_password(f"Royalnet/{secrets_name}", "discord", discord)
    imgur = click.prompt("Imgur API token", default="")
    if imgur:
        keyring.set_password(f"Royalnet/{secrets_name}", "imgur", imgur)
    sentry = click.prompt("Sentry DSN", default="")
    if sentry:
        keyring.set_password(f"Royalnet/{secrets_name}", "sentry", sentry)


if __name__ == "__main__":
    run()
