from royalnet.commands import *


class DndactiveCommand(Command):
    name: str = "dndactive"

    description: str = "Set the active D&D character."

    aliases = ["da", "dnda", "active"]

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        ...
