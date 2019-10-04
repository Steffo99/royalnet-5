import typing
import discord
from ..command import Command
from ..commandinterface import CommandInterface
from ..commandargs import CommandArgs
from ..commanddata import CommandData
from ...utils import NetworkHandler
from ...network import Request, ResponseSuccess
from ..commanderrors import CommandError
if typing.TYPE_CHECKING:
    from ...bots import DiscordBot


class PauseNH(NetworkHandler):
    message_type = "music_pause"

    # noinspection PyProtectedMember
    @classmethod
    async def discord(cls, bot: "DiscordBot", data: dict):
        # Find the matching guild
        if data["guild_name"]:
            guilds: typing.List[discord.Guild] = bot.client.find_guild_by_name(data["guild_name"])
        else:
            guilds = bot.client.guilds
        if len(guilds) == 0:
            raise CommandError("No guilds with the specified name found.")
        if len(guilds) > 1:
            raise CommandError("Multiple guilds with the specified name found.")
        guild = list(bot.client.guilds)[0]
        # Set the currently playing source as ended
        voice_client: discord.VoiceClient = bot.client.find_voice_client_by_guild(guild)
        if not (voice_client.is_playing() or voice_client.is_paused()):
            raise CommandError("There is nothing to pause.")
        # Toggle pause
        resume = voice_client._player.is_paused()
        if resume:
            voice_client._player.resume()
        else:
            voice_client._player.pause()
        return ResponseSuccess({"resumed": resume})


class PauseCommand(Command):
    name: str = "pause"

    description: str = "Mette in pausa o riprende la riproduzione della canzone attuale."

    syntax = "[ [guild] ]"

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        interface.register_net_handler(PauseNH.message_type, PauseNH)

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        guild, = args.match(r"(?:\[(.+)])?")
        response = await self.interface.net_request(Request("music_pause", {"guild_name": guild}), "discord")
        if response["resumed"]:
            await data.reply(f"▶️ Riproduzione ripresa.")
        else:
            await data.reply(f"⏸ Riproduzione messa in pausa.")
