import typing
import pickle
import datetime
from ..command import Command
from ..commandinterface import CommandInterface
from ..commandargs import CommandArgs
from ..commanddata import CommandData
from ...utils import NetworkHandler, asyncify
from ...network import Request, ResponseSuccess
from ...error import *
from ...audio import YtdlDiscord
if typing.TYPE_CHECKING:
    from ...bots import DiscordBot


class PlayNH(NetworkHandler):
    message_type = "music_play"

    @classmethod
    async def discord(cls, bot: "DiscordBot", data: dict):
        """Handle a play Royalnet request. That is, add audio to a PlayMode."""
        # Find the matching guild
        if data["guild_name"]:
            guild = bot.client.find_guild(data["guild_name"])
        else:
            if len(bot.music_data) == 0:
                raise NoneFoundError("No voice clients active")
            if len(bot.music_data) > 1:
                raise TooManyFoundError("Multiple guilds found")
            guild = list(bot.music_data)[0]
        # Ensure the guild has a PlayMode before adding the file to it
        if not bot.music_data.get(guild):
            # TODO: change Exception
            raise Exception("No music_data for this guild")
        # Create url
        ytdl_args = {
            "format": "bestaudio",
            "outtmpl": f"./downloads/{datetime.datetime.now().timestamp()}_%(title)s.%(ext)s"
        }
        # Start downloading
        if data["url"].startswith("http://") or data["url"].startswith("https://"):
            dfiles: typing.List[YtdlDiscord] = await asyncify(YtdlDiscord.create_from_url, data["url"], **ytdl_args)
        else:
            dfiles = await asyncify(YtdlDiscord.create_from_url, f"ytsearch:{data['url']}", **ytdl_args)
        await bot.add_to_music_data(dfiles, guild)
        # Create response dictionary
        response = {
            "videos": [{
                "title": dfile.info.title,
                "discord_embed_pickle": str(pickle.dumps(dfile.info.to_discord_embed()))
            } for dfile in dfiles]
        }
        return ResponseSuccess(response)


class PlayCommand(Command):
    name: str = "play"

    description: str = "Aggiunge una canzone alla coda della chat vocale."

    syntax = "[ [guild] ] (url)"

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        interface.register_net_handler(PlayNH.message_type, PlayNH)

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        guild_name, url = args.match(r"(?:\[(.+)])?\s*<?(.+)>?")
        response = await self.interface.net_request(Request("music_play", {"url": url, "guild_name": guild_name}), "discord")
        if len(response["videos"]) == 0:
            await data.reply(f"⚠️ Nessun video trovato.")
        for video in response["videos"]:
            if self.interface.name == "discord":
                # This is one of the unsafest things ever
                embed = pickle.loads(eval(video["discord_embed_pickle"]))
                await data.message.channel.send(content="▶️ Aggiunto alla coda:", embed=embed)
            else:
                await data.reply(f"▶️ Aggiunto alla coda: [i]{video['title']}[/i]")
