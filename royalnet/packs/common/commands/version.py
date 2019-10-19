from royalnet.commands import *
from royalnet.version import semantic


class VersionCommand(Command):
    name: str = "version"

    description: str = "Get the current Royalnet version."

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        message = f"ℹ️ Royalnet {semantic}\n"
        if "69" in message:
            message += "(Nice.)"
        await data.reply(message)
