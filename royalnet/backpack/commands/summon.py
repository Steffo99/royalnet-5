from royalnet.commands import *
from typing import TYPE_CHECKING, Optional, List
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
            raise UnsupportedError()
        # noinspection PyUnresolvedReferences
        message: discord.Message = data.message
        serf: DiscordSerf = self.interface.bot
        channel_name: Optional[str] = args.joined()
        # If the channel name was passed as an argument...
        if channel_name != "":
            # Try to find the specified channel
            channels: List[discord.abc.GuildChannel] = serf.client.find_channel(channel_name)
            # TODO: if there are multiple channels, try to find the most appropriate one
            # TODO: ensure that the channel is a voice channel
            if len(channels) != 1:
                raise CommandError("Couldn't decide on a channel to connect to.")
            else:
                channel = channels[0]
        else:
            # Try to use the channel in which the command author is in
            voice: Optional[discord.VoiceState] = message.author.voice
            if voice is None:
                raise CommandError("You must be connected to a voice channel to summon the bot without any arguments.")
            channel: discord.VoiceChannel = voice.channel
        # Try to connect to the voice channel
        try:
            client = await channel.connect()
        except asyncio.TimeoutError:
            raise ExternalError("Timed out while trying to connect to the channel")
        except discord.opus.OpusNotLoaded:
            raise ConfigurationError("[c]libopus[/c] is not loaded in the serf")
        except discord.ClientException as e:
            # TODO: handle this someway
            raise
        await asyncio.sleep(6)
        breakpoint()
