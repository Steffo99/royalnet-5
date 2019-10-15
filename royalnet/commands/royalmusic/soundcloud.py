import typing
import pickle
import datetime
import discord
from ..command import Command
from ..commandinterface import CommandInterface
from ..commandargs import CommandArgs
from ..commanddata import CommandData
from ...utils import NetworkHandler, asyncify
from ...network import Request, ResponseSuccess
from ..commanderrors import CommandError
from ...audio import YtdlDiscord

if typing.TYPE_CHECKING:
    from ...bots import DiscordBot


class SoundcloudNH(NetworkHandler):
    message_type = "music_soundcloud"

    @classmethod
    async def discord(cls, bot: "DiscordBot", data: dict):
        """Handle a play Royalnet request. That is, add audio to a PlayMode."""
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
        # Ensure the guild has a PlayMode before adding the file to it
        if not bot.music_data.get(guild):
            raise KeyError("No music data available for this guild.")
        # Create url
        ytdl_args = {
            "format": "bestaudio/best",
            "outtmpl": f"./downloads/{datetime.datetime.now().timestamp()}_%(title)s.%(ext)s"
        }
        # Start downloading
        dfiles: typing.List[YtdlDiscord] = await asyncify(YtdlDiscord.create_from_url, f'scsearch:{data["search"]}',
                                                          **ytdl_args)
        await bot.add_to_music_data(dfiles, guild)
        # Create response dictionary
        response = {
            "videos": [{
                "title": dfile.info.title,
                "discord_embed_pickle": str(pickle.dumps(dfile.info.to_discord_embed()))
            } for dfile in dfiles]
        }
        return ResponseSuccess(response)


class SoundcloudCommand(Command):
    name: str = "soundcloud"

    aliases = ["sc"]

    description: str = "Cerca una canzone su Soundcloud e la aggiunge alla coda della chat vocale."

    syntax = "[ [guild] ] (url)"

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        interface.register_net_handler(SoundcloudNH.message_type, SoundcloudNH)

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        guild_name, search = args.match(r"(?:\[(.+)])?\s*<?(.+)>?")
        if search.startswith("http://") or search.startswith("https://"):
            raise CommandError("SoundcloudCommand only accepts search queries, and you've sent an URL.\n"
                               "If you want to add a song from an url, please use PlayCommand!")
        response = await self.interface.net_request(Request("music_soundcloud", {"search": search,
                                                                                 "guild_name": guild_name}),
                                                    "discord")
        if len(response["videos"]) == 0:
            raise CommandError(f"Il video non può essere scaricato a causa di un blocco imposto da Soundcloud.")
        for video in response["videos"]:
            if self.interface.name == "discord":
                # This is one of the unsafest things ever
                embed = pickle.loads(eval(video["discord_embed_pickle"]))
                await data.message.channel.send(content="▶️ Aggiunto alla coda:", embed=embed)
            else:
                await data.reply(f"▶️ Aggiunto alla coda: [i]{video['title']}[/i]")
