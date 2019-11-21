from typing import Optional
from royalnet.commands import *
from royalnet.serf.discord import DiscordSerf

try:
    import discord
except ImportError:
    discord = None


class SummonEvent(Event):
    name = "summon"

    async def run(self, *, channel_name: str, guild_id: Optional[int] = None, user_id: Optional[int] = None, **kwargs):
        if not isinstance(self.serf, DiscordSerf):
            raise UnsupportedError("Summon can't be called on interfaces other than Discord.")
        if discord is None:
            raise UnsupportedError("'discord' extra is not installed.")
        # Find the guild
        if guild_id is not None:
            guild: Optional["discord.Guild"] = self.serf.client.get_guild(guild_id)
        else:
            guild = None
        # Find the member
        if user_id is not None and guild is not None:
            member = guild.get_member(user_id=user_id)
        else:
            member = None
        # Find accessible_to
        accessible_to = [self.serf.client.user]
        if member is not None:
            accessible_to.append(member)
        # Find the channel
        channel: Optional["discord.VoiceChannel"] = self.serf.find_channel(channel_type=discord.VoiceChannel,
                                                                           name=channel_name,
                                                                           guild=guild,
                                                                           accessible_to=accessible_to,
                                                                           required_permissions=["connect", "speak"])
        if channel is None:
            raise InvalidInputError("No channels found with the specified name.")
        # Connect to the channel
        await self.serf.voice_connect(channel)
        # Find the created bard
        bard = self.serf.bards[channel.guild]
        bard_peek = await bard.peek()
        # Reply to the request
        return {
            "channel": {
                "id": channel.id,
                "name": channel.name,
                "guild": {
                    "name": channel.guild.name,
                },
            },
            "bard": {
                "type": bard.__class__.__qualname__,
                "peek": bard_peek,
            }
        }
