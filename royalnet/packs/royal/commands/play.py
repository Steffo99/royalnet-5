import typing
import pickle
import datetime
import discord
from royalnet.commands import *
from royalnet.utils import asyncify
from royalnet.audio import YtdlDiscord
from royalnet.bots import DiscordBot


class PlayCommand(Command):
    name: str = "play"

    aliases = ["p"]

    description: str = "Aggiunge un url alla coda della chat vocale."

    syntax = "[ [guild] ] (url)"

    @staticmethod
    async def _legacy_play_handler(bot: "DiscordBot", guild_name: typing.Optional[str], url: str):
        """Handle a play Royalnet request. That is, add audio to a PlayMode."""
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
        # Ensure the guild has a PlayMode before adding the file to it
        if not bot.music_data.get(guild):
            # TODO: change Exception
            raise Exception("No music_data for this guild")
        # Create url
        ytdl_args = {
            "format": "bestaudio/best",
            "outtmpl": f"./downloads/{datetime.datetime.now().timestamp()}_%(title)s.%(ext)s"
        }
        # Start downloading
        dfiles: typing.List[YtdlDiscord] = await asyncify(YtdlDiscord.create_from_url, url, **ytdl_args)
        await bot.add_to_music_data(dfiles, guild)
        # Create response dictionary
        response = {
            "videos": [{
                "title": dfile.info.title,
                "discord_embed_pickle": str(pickle.dumps(dfile.info.to_discord_embed()))
            } for dfile in dfiles]
        }
        return response

    _event_name = "_legacy_play"

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        if interface.name == "discord":
            interface.register_herald_action(self._event_name, self._legacy_play_handler)

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        guild_name, url = args.match(r"(?:\[(.+)])?\s*<?(.+)>?")
        if not (url.startswith("http://") or url.startswith("https://")):
            raise CommandError("PlayCommand only accepts URLs.\n"
                               "If you want to search a song on YouTube or Soundcloud, please use YoutubeCommand"
                               " or SoundcloudCommand!")
        response: dict = await self.interface.call_herald_action("discord", self._event_name, {
                                                                     "guild_name": guild_name,
                                                                     "url": url
                                                                 })
        if len(response["videos"]) == 0:
            raise CommandError(f"Nessun file trovato.")
        for video in response["videos"]:
            if self.interface.name == "discord":
                # This is one of the unsafest things ever
                embed = pickle.loads(eval(video["discord_embed_pickle"]))
                await data.message.channel.send(content="▶️ Aggiunto alla coda:", embed=embed)
            else:
                await data.reply(f"▶️ Aggiunto alla coda: [i]{video['title']}[/i]")
