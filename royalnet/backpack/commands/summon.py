from royalnet.commands import *
from typing import TYPE_CHECKING, Optional, List, Union
import asyncio

try:
    import discord
except ImportError:
    discord = None

if TYPE_CHECKING:
    from royalnet.serf.discord import DiscordSerf


class SummonCommand(Command):
    # TODO: possibly move this in another pack

    name: str = "summon"

    description = "Connect the bot to a Discord voice channel."

    syntax = "[channelname]"

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        if self.interface.name == "discord":
            msg: Optional["discord.Message"] = data.message
            member: Optional["discord.Member"] = msg.author
            guild: Optional["discord.Guild"] = msg.guild
        else:
            member = None
            guild = None
        name = args.joined()
        response: dict = await self.interface.call_herald_event("discord", "summon", **{
            "channel_name": name,
            "guild_id": guild.id if guild is not None else None,
            "user_id": member.id if member is not None else None,
        })
        await data.reply(f"✅ Connected to [b]#{response['channel']['name']}[/b]"
                         f" in [i]{response['channel']['guild']['name']}[/i]!")
