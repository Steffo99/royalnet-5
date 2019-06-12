import typing
import discord
from ..utils import Command, Call, NetworkHandler
from ..network import Request, ResponseSuccess
from ..error import NoneFoundError
if typing.TYPE_CHECKING:
    from ..bots import DiscordBot


class SummonNH(NetworkHandler):
    message_type = "music_summon"

    @classmethod
    async def discord(cls, bot: "DiscordBot", data: dict):
        """Handle a summon Royalnet request. That is, join a voice channel, or move to a different one if that is not possible."""
        channel = bot.client.find_channel_by_name(data["channel_name"])
        if not isinstance(channel, discord.VoiceChannel):
            raise NoneFoundError("Channel is not a voice channel")
        bot.loop.create_task(bot.client.vc_connect_or_move(channel))
        return ResponseSuccess()


class SummonCommand(Command):

    command_name = "summon"
    command_description = "Evoca il bot in un canale vocale."
    command_syntax = "[channelname]"

    network_handlers = [SummonNH]

    @classmethod
    async def common(cls, call: Call):
        channel_name: str = call.args[0].lstrip("#")
        await call.net_request(Request("music_summon", {"channel_name": channel_name}), "discord")
        await call.reply(f"✅ Mi sono connesso in [c]#{channel_name}[/c].")

    @classmethod
    async def discord(cls, call: Call):
        bot = call.interface_obj.client
        message: discord.Message = call.kwargs["message"]
        channel_name: str = call.args.optional(0)
        if channel_name:
            guild: typing.Optional[discord.Guild] = message.guild
            if guild is not None:
                channels: typing.List[discord.abc.GuildChannel] = guild.channels
            else:
                channels = bot.get_all_channels()
            matching_channels: typing.List[discord.VoiceChannel] = []
            for channel in channels:
                if isinstance(channel, discord.VoiceChannel):
                    if channel.name == channel_name:
                        matching_channels.append(channel)
            if len(matching_channels) == 0:
                await call.reply("⚠️ Non esiste alcun canale vocale con il nome specificato.")
                return
            elif len(matching_channels) > 1:
                await call.reply("⚠️ Esiste più di un canale vocale con il nome specificato.")
                return
            channel = matching_channels[0]
        else:
            author: discord.Member = message.author
            voice: typing.Optional[discord.VoiceState] = author.voice
            if voice is None:
                await call.reply("⚠️ Non sei connesso a nessun canale vocale!")
                return
            channel = voice.channel
        await bot.vc_connect_or_move(channel)
        await call.reply(f"✅ Mi sono connesso in [c]#{channel.name}[/c].")
