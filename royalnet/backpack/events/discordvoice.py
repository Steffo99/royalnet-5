import asyncio
from typing import Dict, List, Optional
from royalnet.commands import *
from royalnet.serf import Serf
from royalnet.serf.discord import DiscordSerf
from royalnet.bard import DiscordBard
from royalnet.bard.implementations import *

try:
    import discord
except ImportError:
    discord = None


class DiscordvoiceEvent(Event):
    name: str = "discordvoice"

    def __init__(self, serf: Serf):
        super().__init__(serf)
        self.bards: Dict["discord.Guild", DiscordBard] = {}

    async def run(self, data: dict):
        if not isinstance(self.serf, DiscordSerf):
            raise ValueError("`discordvoice` event cannot run on other serfs.")

        operation = data["operation"]

        if operation == "summon":
            channel_name: str = data["data"]["channel_name"]
            member_id: int = data["data"].get("member_id")
            guild_id: int = data["data"].get("guild_id")
            client: discord.Client = self.serf.client

            # Get the guild, if it exists
            if guild_id is not None:
                guild: Optional[discord.Guild] = client.get_guild(guild_id)
            else:
                guild = None

            # Get the member, if it exists
            if member_id is not None and guild is not None:
                member: Optional[discord.Member] = guild.get_member(member_id)
            else:
                member = None

            # Try to find all possible channels
            channels: List[discord.VoiceChannel] = []
            for ch in client.get_all_channels():
                guild: discord.Guild = ch.guild
                # Ensure the channel is a voice channel
                if not isinstance(ch, discord.VoiceChannel):
                    continue
                # Ensure the channel starts with the requested name
                ch_name: str = ch.name
                if not ch_name.startswith(channel_name):
                    continue
                # Ensure that the command author can access the channel
                if member is not None:
                    member_permissions: discord.Permissions = ch.permissions_for(member)
                    if not (member_permissions.connect and member_permissions.speak):
                        continue
                # Ensure that the bot can access the channel
                bot_member = guild.get_member(client.user.id)
                bot_permissions: discord.Permissions = ch.permissions_for(bot_member)
                if not (bot_permissions.connect and bot_permissions.speak):
                    continue
                # Found one!
                channels.append(ch)

            # Ensure at least a single channel is returned
            if len(channels) == 0:
                raise InvalidInputError("Could not find any channel to connect to.")
            else:
                # Give priority to channels in the current guild
                filter_by_guild = False
                for ch in channels:
                    if ch.guild == guild:
                        filter_by_guild = True
                        break
                if filter_by_guild:
                    new_channels = []
                    for ch in channels:
                        if ch.guild == guild:
                            new_channels.append(ch)
                    channels = new_channels

                # Give priority to channels with the most people
                def people_count(c: discord.VoiceChannel):
                    return len(c.members)

                channels.sort(key=people_count, reverse=True)

                channel = channels[0]

            # Try to connect to the voice channel
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                raise ExternalError("Timed out while trying to connect to the channel")
            except discord.opus.OpusNotLoaded:
                raise ConfigurationError("[c]libopus[/c] is not loaded in the serf")
            except discord.ClientException:
                # The bot is already connected to a voice channel
                # TODO: safely move the bot somewhere else
                raise CommandError("The bot is already connected in another channel.\n"
                                   " Please disconnect it before resummoning!")


            return {
                "connected": True
            }
        else:
            raise ValueError(f"Invalid operation received: {operation}")
