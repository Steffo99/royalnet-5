import toml
import importlib
import click

p = click.echo


@click.command()
@click.option("-c", "--config-filename", default="./config.toml", type=click.Path(exists=True),
              help="The filename of the Royalnet configuration file.")
@click.option("-f", "--file-format", type=str, help="The name of the format that should be generated.")
def run(config_filename, file_format):
    with open(config_filename, "r") as t:
        config: dict = toml.load(t)

    # Import packs
    packs_cfg = config["Packs"]
    pack_names = packs_cfg["active"]
    packs = {}
    for pack_name in pack_names:
        try:
            packs[pack_name] = importlib.import_module(pack_name)
        except ImportError as e:
            p(f"Skipping `{pack_name}`: {e}", err=True)
            continue

    if file_format == "botfather":
        for pack_name in packs:
            pack = packs[pack_name]
            lines = []

            try:
                commands = pack.available_commands
            except AttributeError:
                p(f"Pack `{pack}` does not have the `available_commands` attribute.", err=True)
                continue
            for command in commands:
                lines.append(f"{command.name} - {command.description}")

            lines.sort()
            for line in lines:
                p(line)

    elif file_format == "markdown":
        for pack_name in packs:
            pack = packs[pack_name]
            p(f"# {pack_name}")
            p("")

            try:
                commands = pack.available_commands
            except AttributeError:
                p(f"Pack `{pack}` does not have the `available_commands` attribute.", err=True)
            else:
                p(f"## Commands")
                p("")
                for command in commands:
                    p(f"### `{command.name}`")
                    p("")
                    p(f"{command.description}")
                    p("")
                    if len(command.aliases) > 0:
                        p(f"> Aliases: {''.join(['`' + alias + '` ' for alias in command.aliases])}")
                        p("")

            try:
                events = pack.available_events
            except AttributeError:
                p(f"Pack `{pack}` does not have the `available_events` attribute.", err=True)
            else:
                p(f"## Events")
                p("")
                for event in events:
                    p(f"### `{event.name}`")
                    p("")

            try:
                page_stars = pack.available_page_stars
            except AttributeError:
                p(f"Pack `{pack}` does not have the `available_page_stars` attribute.", err=True)
            else:
                p(f"## Page Stars")
                p("")
                for page_star in page_stars:
                    p(f"### `{page_star.path}`")
                    p("")

            try:
                exc_stars = pack.available_exception_stars
            except AttributeError:
                p(f"Pack `{pack}` does not have the `available_exception_stars` attribute.", err=True)
            else:
                p(f"## Exception Stars")
                p("")
                for exc_star in exc_stars:
                    p(f"### `{exc_star.error}`")
                    p("")

            try:
                tables = pack.available_tables
            except AttributeError:
                p(f"Pack `{pack}` does not have the `available_tables` attribute.", err=True)
            else:
                p(f"## Tables")
                p("")
                for table in tables:
                    p(f"### `{table.__tablename__}`")
                    p("")
                    # TODO: list columns

    else:
        raise click.ClickException("Unknown format")


if __name__ == "__main__":
    run()
