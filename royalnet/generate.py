import toml
import importlib
import click
from .version import semantic

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
            packs[pack_name] = {
                "commands": importlib.import_module(f"{pack_name}.commands"),
                "events": importlib.import_module(f"{pack_name}.events"),
                "stars": importlib.import_module(f"{pack_name}.stars"),
                "tables": importlib.import_module(f"{pack_name}.tables"),
            }
        except ImportError as e:
            p(f"Skipping `{pack_name}`: {e}", err=True)
            continue

    if file_format == "botfather":
        for pack_name in packs:
            pack = packs[pack_name]
            lines = []

            try:
                commands = pack["commands"].available_commands
            except AttributeError:
                p(f"Pack `{pack}` does not have the `available_commands` attribute.", err=True)
                continue
            for command in commands:
                lines.append(f"{command.name} - {command.description}")

            lines.sort()
            for line in lines:
                p(line)

    else:
        raise click.ClickException("Unknown format")


if __name__ == "__main__":
    run()
