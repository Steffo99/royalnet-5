import typing
import discord
from royalnet.commands import *
from royalnet.audio.playmodes import Playlist, Pool, Layers
from royalnet.bots import DiscordBot


class PlaymodeCommand(Command):
    name: str = "playmode"

    aliases = ["pm", "mode"]

    description: str = "Cambia modalità di riproduzione per la chat vocale."

    syntax = "[ [guild] ] {mode}"

    @staticmethod
    async def _legacy_playmode_handler(bot: "DiscordBot", guild_name: typing.Optional[str], mode_name: str):
        """Handle a playmode Royalnet request. That is, change current PlayMode."""
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
        # Delete the previous PlayMode, if it exists
        if bot.music_data[guild] is not None:
            bot.music_data[guild].delete()
        # Create the new PlayMode
        if mode_name == "playlist":
            bot.music_data[guild] = Playlist()
        elif mode_name == "pool":
            bot.music_data[guild] = Pool()
        elif mode_name == "layers":
            bot.music_data[guild] = Layers()
        else:
            raise CommandError("Unknown PlayMode specified.")
        return {}

    _event_name = "_legacy_playmode"

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        if interface.name == "discord":
            interface.register_herald_action(self._event_name, self._legacy_playmode_handler)

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        guild_name, mode_name = args.match(r"(?:\[(.+)])?\s*(\S+)\s*")
        await self.interface.call_herald_action("discord", self._event_name, {
                                                    "guild_name": guild_name,
                                                    "mode_name": mode_name
                                                })
        await data.reply(f"🔃 Impostata la modalità di riproduzione a: [c]{mode_name}[/c].")
