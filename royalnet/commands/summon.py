import typing
import discord
from ..utils import Command, Call
from ..network import Message


class SummonMessage(Message):
    def __init__(self, channel_name: str):
        self.channel_name: str = channel_name


class SummonSuccessful(Message):
    pass


class SummonError(Message):
    def __init__(self, reason: str):
        self.reason: str = reason


class SummonCommand(Command):

    command_name = "summon"
    command_description = "Evoca il bot in un canale vocale."
    command_syntax = "[channelname]"

    @classmethod
    async def common(cls, call: Call):
        channel_name: str = call.args[0].lstrip("#")
        response: typing.Union[SummonSuccessful, SummonError] = await call.net_request(SummonMessage(channel_name), "discord")
        if isinstance(response, SummonError):
            await call.reply(f"⚠️ Si è verificato un'errore nella richiesta di connessione:\n[c]{response.reason}[/c]")
            return
        elif isinstance(response, SummonSuccessful):
            await call.reply(f"✅ Mi sono connesso in [c]#{channel_name}[/c].")
            return
        raise TypeError(f"Received unexpected response type while summoning the bot: {response.__class__.__name__}")

    @classmethod
    async def discord(cls, call: Call):
        bot = call.interface_obj.bot
        message: discord.Message = call.kwargs["message"]
        channel_name: str = call.args.optional(0)
        if channel_name:
            guild: typing.Optional[discord.Guild] = message.guild
            channels: typing.List[discord.abc.GuildChannel]
            if guild is not None:
                channels = guild.channels
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
