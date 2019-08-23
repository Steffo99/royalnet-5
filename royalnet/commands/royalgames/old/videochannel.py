import discord
import typing
from ..utils import Command, Call


class VideochannelCommand(Command):

    command_name = "videochannel"
    command_description = "Converti il canale vocale in un canale video."
    command_syntax = "[channelname]"

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
            if author.is_on_mobile():
                await call.reply(f"📹 Per entrare in modalità video, clicca qui: <https://discordapp.com/channels/{channel.guild.id}/{channel.id}>\n[b]Attenzione: la modalità video non funziona su Discord per Android e iOS![/b]")
                return
        await call.reply(f"📹 Per entrare in modalità video, clicca qui: <https://discordapp.com/channels/{channel.guild.id}/{channel.id}>")
