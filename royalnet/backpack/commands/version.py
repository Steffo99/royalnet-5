import royalnet
from royalnet.commands import *


class VersionCommand(Command):
    name: str = "version"

    description: str = "Display the current Royalnet version."

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        # noinspection PyUnreachableCode
        if __debug__:
            message = f"ℹ️ Royalnet {royalnet.__version__} (debug)\n"
        else:
            message = f"ℹ️ Royalnet {royalnet.__version__}\n"
        if "69" in message:
            message += "(Nice.)"
        await data.reply(message)
