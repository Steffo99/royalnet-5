import royalnet.version
from royalnet.commands import *


class RoyalnetversionCommand(Command):
    name: str = "royalnetversion"

    description: str = "Display the current Royalnet version."

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        # noinspection PyUnreachableCode
        if __debug__:
            message = f"ℹ️ Royalnet [url=https://github.com/Steffo99/royalnet/]Unreleased[/url]\n"
        else:
            message = f"ℹ️ Royalnet [url=https://github.com/Steffo99/royalnet/releases/tag/{royalnet.version.semantic}]{royalnet.version.semantic}[/url]\n"
        if "69" in royalnet.version.semantic:
            message += "(Nice.)"
        await data.reply(message)
