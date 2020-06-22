from typing import *
import royalnet
import royalnet.commands as rc
import royalnet.utils as ru
from ..tables import User


class RoyalnetaliasesCommand(rc.Command):
    name: str = "royalnetaliases"

    description: str = "Display your Royalnet aliases."

    syntax: str = ""

    async def run(self, args: rc.CommandArgs, data: rc.CommandData) -> None:
        if name := args.optional(0) is not None:
            user = await User.find(alchemy=self.alchemy, session=data.session, identifier=name)
        else:
            user = await data.get_author(error_if_none=True)

        msg = [
            "👤 You currently have these aliases:",
            *list(map(lambda r: f"- {r}", user.aliases))
        ]

        await data.reply("\n".join(msg))
