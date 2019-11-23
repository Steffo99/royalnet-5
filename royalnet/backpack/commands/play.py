from royalnet.commands import *
from typing import TYPE_CHECKING, Optional, List, Union
import asyncio

try:
    import discord
except ImportError:
    discord = None

if TYPE_CHECKING:
    from royalnet.serf.discord import DiscordSerf


class PlayCommand(Command):
    # TODO: possibly move this in another pack

    name: str = "play"

    description = ""

    syntax = "[url]"

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        url = args.joined()
        response: dict = await self.interface.call_herald_event("discord", "play", url=url)
        await data.reply("blah")
