from typing import *
import royalnet
import royalnet.commands as rc
import royalnet.utils as ru
from ..tables.telegram import Telegram
from ..tables.discord import Discord


class RoyalnetaliasesCommand(rc.Command):
    name: str = "royalnetaliases"

    description: str = "Display your Royalnet aliases."

    syntax: str = ""

    async def run(self, args: rc.CommandArgs, data: rc.CommandData) -> None:
        author = await data.get_author(error_if_none=True)

        msg = [
            "👤 You currently have these aliases:",
            *list(map(lambda r: f"- {r}", author.aliases))
        ]

        await data.reply("\n".join(msg))
