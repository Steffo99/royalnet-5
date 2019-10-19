import typing
import discord
from royalnet.commands import *
from royalnet.bots import DiscordBot


class SkipCommand(Command):
    name: str = "skip"

    aliases = ["s", "next", "n"]

    description: str = "Salta la canzone attualmente in riproduzione in chat vocale."

    syntax: str = "[ [guild] ]"

    @staticmethod
    async def _legacy_skip_handler(bot: "DiscordBot", guild_name: typing.Optional[str]):
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
            raise CommandError("Nothing to skip")
        # noinspection PyProtectedMember
        voice_client._player.stop()
        return {}

    _event_name = "_legacy_skip"

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        if interface.name == "discord":
            interface.register_herald_action(self._event_name, self._legacy_skip_handler)

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        guild_name, = args.match(r"(?:\[(.+)])?")
        await self.interface.call_herald_action("discord", self._event_name, {
                                                    "guild_name": guild_name
                                                })
        await data.reply(f"⏩ Richiesto lo skip della canzone attuale.")
