import typing
import discord
from royalnet.commands import *
from royalnet.bots import DiscordBot


class PauseCommand(Command):
    name: str = "pause"

    description: str = "Mette in pausa o riprende la riproduzione della canzone attuale."

    syntax = "[ [guild] ]"

    @staticmethod
    async def _legacy_pause_handler(bot: DiscordBot, guild_name: typing.Optional[str]):
        # Find the matching guild
        if guild_name:
            guilds: typing.List[discord.Guild] = bot.client.find_guild_by_name(guild_name)
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
        return {"resumed": resume}

    _event_name = "_legacy_pause"

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        if interface.name == "discord":
            interface.register_herald_action(self._event_name, self._legacy_pause_handler)

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        guild_name, = args.match(r"(?:\[(.+)])?")
        response = await self.interface.call_herald_action("discord", self._event_name, {
                                                               "guild_name": guild_name
                                                           })
        if response["resumed"]:
            await data.reply(f"▶️ Riproduzione ripresa.")
        else:
            await data.reply(f"⏸ Riproduzione messa in pausa.")
