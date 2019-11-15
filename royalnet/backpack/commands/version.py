import royalnet
from royalnet.commands import *


class VersionCommand(Command):
    name: str = "version"

    description: str = "Get the current Royalnet version."

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        message = f"ℹ️ Royalnet {royalnet.__version__}\n"
        if "69" in message:
            message += "(Nice.)"
        await data.reply(message)
