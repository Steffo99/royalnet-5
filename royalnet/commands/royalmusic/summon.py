import typing
import discord
from ..command import Command
from ..commandinterface import CommandInterface
from ..commandargs import CommandArgs
from ..commanddata import CommandData
from ...utils import NetworkHandler
from ...network import Request, ResponseSuccess
from ...error import NoneFoundError
if typing.TYPE_CHECKING:
    from ...bots import DiscordBot


class SummonNH(NetworkHandler):
    message_type = "music_summon"

    @classmethod
    async def discord(cls, bot: "DiscordBot", data: dict):
        """Handle a summon Royalnet request.
         That is, join a voice channel, or move to a different one if that is not possible."""
        channel = bot.client.find_channel_by_name(data["channel_name"])
        if not isinstance(channel, discord.VoiceChannel):
            raise NoneFoundError("Channel is not a voice channel")
        bot.loop.create_task(bot.client.vc_connect_or_move(channel))
        return ResponseSuccess()


class SummonCommand(Command):
    name: str = "summon"

    description: str = "Evoca il bot in un canale vocale."

    syntax: str = "[nomecanale]"

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        interface.register_net_handler(SummonNH.message_type, SummonNH)

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        if self.interface.name == "discord":
            bot = self.interface.bot.client
            message: discord.Message = data.message
            channel_name: str = args.optional(0)
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
                    await data.reply("⚠️ Non esiste alcun canale vocale con il nome specificato.")
                    return
                elif len(matching_channels) > 1:
                    await data.reply("⚠️ Esiste più di un canale vocale con il nome specificato.")
                    return
                channel = matching_channels[0]
            else:
                author: discord.Member = message.author
                try:
                    voice: typing.Optional[discord.VoiceState] = author.voice
                except AttributeError:
                    await data.reply("⚠️ Non puoi evocare il bot da una chat privata!")
                    return
                if voice is None:
                    await data.reply("⚠️ Non sei connesso a nessun canale vocale!")
                    return
                channel = voice.channel
            await bot.vc_connect_or_move(channel)
            await data.reply(f"✅ Mi sono connesso in [c]#{channel.name}[/c].")
        else:
            channel_name: str = args[0].lstrip("#")
            await self.interface.net_request(Request(SummonNH.message_type, {"channel_name": channel_name}), "discord")
            await data.reply(f"✅ Mi sono connesso in [c]#{channel_name}[/c].")
