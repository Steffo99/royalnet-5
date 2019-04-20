import typing
import discord
from ..network import Message, RequestSuccessful
from ..utils import Command, Call, NetworkHandler
from ..error import TooManyFoundError, NoneFoundError
if typing.TYPE_CHECKING:
    from ..bots import DiscordBot


class SkipMessage(Message):
    def __init__(self, guild_name: typing.Optional[str] = None):
        self.guild_name: typing.Optional[str] = guild_name


class SkipNH(NetworkHandler):
    message_type = SkipMessage

    @classmethod
    async def discord(cls, bot: "DiscordBot", message: SkipMessage):
        # Find the matching guild
        if message.guild_name:
            guild = bot.client.find_guild_by_name(message.guild_name)
        else:
            if len(bot.music_data) != 1:
                raise TooManyFoundError("Multiple guilds found")
            guild = list(bot.music_data)[0]
        # Set the currently playing source as ended
        voice_client: discord.VoiceClient = bot.client.find_voice_client_by_guild(guild)
        if not voice_client.is_playing():
            raise NoneFoundError("Nothing to skip")
        # noinspection PyProtectedMember
        voice_client._player.stop()
        return RequestSuccessful()


class SkipCommand(Command):

    command_name = "skip"
    command_description = "Salta la canzone attualmente in riproduzione in chat vocale."
    command_syntax = "[ [guild] ]"

    network_handlers = [SkipNH]

    @classmethod
    async def common(cls, call: Call):
        guild, = call.args.match(r"(?:\[(.+)])?")
        await call.net_request(SkipMessage(guild), "discord")
        await call.reply(f"✅ Richiesta lo skip della canzone attuale..")
