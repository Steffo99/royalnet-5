import typing
import discord
from ..network import Request, ResponseSuccess
from ..utils import Command, Call, NetworkHandler
from ..error import TooManyFoundError, NoneFoundError
if typing.TYPE_CHECKING:
    from ..bots import DiscordBot


class SkipNH(NetworkHandler):
    message_type = "music_skip"

    @classmethod
    async def discord(cls, bot: "DiscordBot", data: dict):
        # Find the matching guild
        if data["guild_name"]:
            guild = bot.client.find_guild_by_name(data["guild_name"])
        else:
            if len(bot.music_data) == 0:
                raise NoneFoundError("No voice clients active")
            if len(bot.music_data) > 1:
                raise TooManyFoundError("Multiple guilds found")
            guild = list(bot.music_data)[0]
        # Set the currently playing source as ended
        voice_client: discord.VoiceClient = bot.client.find_voice_client_by_guild(guild)
        if not (voice_client.is_playing() or voice_client.is_paused()):
            raise NoneFoundError("Nothing to skip")
        # noinspection PyProtectedMember
        voice_client._player.stop()
        return ResponseSuccess()


class SkipCommand(Command):

    command_name = "skip"
    command_description = "Salta la canzone attualmente in riproduzione in chat vocale."
    command_syntax = "[ [guild] ]"

    network_handlers = [SkipNH]

    @classmethod
    async def common(cls, call: Call):
        guild, = call.args.match(r"(?:\[(.+)])?")
        await call.net_request(Request("music_skip", {"guild_name": guild}), "discord")
        await call.reply(f"✅ Richiesto lo skip della canzone attuale.")
