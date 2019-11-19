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
        try:
            await self.interface.call_herald_event("discord", "discordvoice", {
                "operation": "summon",
                "data": {
                    "channel_name": args.joined(),
                    "member_id": member.id if member is not None else None,
                    "guild_id": guild.id if member is not None else None,
                }
            })
        except Exception as e:
            breakpoint()
        await data.reply(f"✅ Connesso alla chat vocale.")
