import typing
import discord
from ..network import Request, ResponseSuccess
from ..utils import Command, Call, NetworkHandler
from ..error import TooManyFoundError, NoneFoundError
if typing.TYPE_CHECKING:
    from ..bots import DiscordBot


class PauseNH(NetworkHandler):
    message_type = "music_pause"

    # noinspection PyProtectedMember
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
            raise NoneFoundError("Nothing to pause")
        # Toggle pause
        resume = voice_client._player.is_paused()
        if resume:
            voice_client._player.resume()
        else:
            voice_client._player.pause()
        return ResponseSuccess({"resume": resume})


class PauseCommand(Command):

    command_name = "pause"
    command_description = "Mette in pausa o riprende la riproduzione della canzone attuale."
    command_syntax = "[ [guild] ]"

    network_handlers = [PauseNH]

    @classmethod
    async def common(cls, call: Call):
        guild, = call.args.match(r"(?:\[(.+)])?")
        response = await call.net_request(Request("music_pause", {"guild_name": guild}), "discord")
        if response["resume"]:
            await call.reply(f"▶️ Riproduzione ripresa.")
        else:
            await call.reply(f"⏸ Riproduzione messa in pausa.")
