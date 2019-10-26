import typing
import pickle
import datetime
import discord
from royalnet.commands import *
from royalnet.utils import asyncify
from royalnet.audio import YtdlDiscord
from royalnet.bots import DiscordBot


class SoundcloudCommand(Command):
    name: str = "soundcloud"

    aliases = ["sc"]

    description: str = "Cerca una canzone su Soundcloud e la aggiunge alla coda della chat vocale."

    syntax = "[ [guild] ] {url}"

    @staticmethod
    async def _legacy_soundcloud_handler(bot: "DiscordBot", guild_name: typing.Optional[str], search: str):
        # Find the matching guild
        if guild_name:
            guilds: typing.List[discord.Guild] = bot.client.find_guild_by_name(guild_name)
        else:
            guilds = bot.client.guilds
        if len(guilds) == 0:
            raise CommandError("Server non trovato.")
        if len(guilds) > 1:
            raise CommandError("Il nome del server è ambiguo.")
        guild = list(bot.client.guilds)[0]
        # Ensure the guild has a PlayMode before adding the file to it
        if not bot.music_data.get(guild):
            raise CommandError("Il bot non è in nessun canale vocale.")
        # Create url
        ytdl_args = {
            "format": "bestaudio/best",
            "outtmpl": f"./downloads/{datetime.datetime.now().timestamp()}_%(title)s.%(ext)s"
        }
        # Start downloading
        dfiles: typing.List[YtdlDiscord] = await asyncify(YtdlDiscord.create_from_url, f'scsearch:{search}',
                                                          **ytdl_args)
        await bot.add_to_music_data(dfiles, guild)
        # Create response dictionary
        return {
            "videos": [{
                "title": dfile.info.title,
                "discord_embed_pickle": str(pickle.dumps(dfile.info.to_discord_embed()))
            } for dfile in dfiles]
        }

    _event_name = "_legacy_soundcloud"

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        if interface.name == "discord":
            interface.register_herald_action(self._event_name, self._legacy_soundcloud_handler)

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        guild_name, search = args.match(r"(?:\[(.+)])?\s*<?(.+)>?")
        if search.startswith("http://") or search.startswith("https://"):
            raise CommandError(f"Il comando [c]{self.interface.prefix}soundcloud[/c] funziona solo per cercare audio su"
                               f" Soundcloud con un dato nome.\n"
                               f"Se vuoi riprodurre una canzone da un URL, usa [c]{self.interface.prefix}play[/c]!")
        response = await self.interface.call_herald_action("discord", self._event_name, {
                                                               "guild_name": guild_name,
                                                               "search": search
                                                           })
        if len(response["videos"]) == 0:
            raise CommandError(f"Il video non può essere scaricato a causa di un blocco imposto da Soundcloud.")
        for video in response["videos"]:
            if self.interface.name == "discord":
                # This is one of the unsafest things ever
                embed = pickle.loads(eval(video["discord_embed_pickle"]))
                await data.message.channel.send(content="▶️ Aggiunto alla coda:", embed=embed)
            else:
                await data.reply(f"▶️ Aggiunto alla coda: [i]{video['title']}[/i]")
