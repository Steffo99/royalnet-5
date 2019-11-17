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
    name: str = "summon"

    description = "Connect the bot to a Discord voice channel."

    syntax = "[channelname]"

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        # This command only runs on Discord!
        if self.interface.name != "discord":
            # TODO: use a Herald Event to remotely connect the bot
            raise UnsupportedError()
        if discord is None:
            raise ConfigurationError("'discord' extra is not installed.")
        # noinspection PyUnresolvedReferences
        message: discord.Message = data.message
        member: Union[discord.User, discord.Member] = message.author
        serf: DiscordSerf = self.interface.serf
        client: discord.Client = serf.client
        channel_name: Optional[str] = args.joined()

        # If the channel name was passed as an argument...
        if channel_name != "":
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
                if guild.get_member(member.id) is None:
                    continue
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
            elif len(channels) == 1:
                channel = channels[0]
            else:
                # Give priority to channels in the current guild
                filter_by_guild = False
                for ch in channels:
                    if ch.guild == message.guild:
                        filter_by_guild = True
                        break
                if filter_by_guild:
                    new_channels = []
                    for ch in channels:
                        if ch.guild == message.guild:
                            new_channels.append(ch)
                    channels = new_channels

                # Give priority to channels with the most people
                def people_count(c: discord.VoiceChannel):
                    return len(c.members)
                channels.sort(key=people_count, reverse=True)

                channel = channels[0]

        else:
            # Try to use the channel in which the command author is in
            voice: Optional[discord.VoiceState] = message.author.voice
            if voice is None:
                raise UserError("You must be connected to a voice channel to summon the bot without any arguments.")
            channel: discord.VoiceChannel = voice.channel

        # Try to connect to the voice channel
        try:
            await channel.connect()
        except asyncio.TimeoutError:
            raise ExternalError("Timed out while trying to connect to the channel")
        except discord.opus.OpusNotLoaded:
            raise ConfigurationError("[c]libopus[/c] is not loaded in the serf")
        except discord.ClientException as e:
            # The bot is already connected to a voice channel
            # TODO: safely move the bot somewhere else
            raise CommandError("The bot is already connected in another channel.")

        await data.reply(f"✅ Connected to <#{channel.id}>!")
