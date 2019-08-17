import typing
import asyncio
import pickle
from ..utils import Command, Call, NetworkHandler, asyncify
from ..network import Request, ResponseSuccess
from ..error import TooManyFoundError, NoneFoundError
from ..audio import YtdlDiscord
if typing.TYPE_CHECKING:
    from ..bots import DiscordBot


ytdl_args = {
    "format": "bestaudio",
    "outtmpl": f"./downloads/%(title)s.%(ext)s"
}


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
        # Start downloading
        if data["url"].startswith("http://") or data["url"].startswith("https://"):
            dfiles: typing.List[YtdlDiscord] = await asyncify(YtdlDiscord.create_and_ready_from_url, data["url"], **ytdl_args)
        else:
            dfiles = await asyncify(YtdlDiscord.create_and_ready_from_url, f"ytsearch:{data['url']}", **ytdl_args)
        await bot.add_to_music_data(dfiles, guild)
        # Create response dictionary
        response = {
            "videos": [{
                "title": dfile.info.title,
                "discord_embed_pickle": str(pickle.dumps(dfile.info.to_discord_embed()))
            } for dfile in dfiles]
        }
        return ResponseSuccess(response)


async def notify_on_timeout(call: Call, url: str, time: float, repeat: bool = False):
    """Send a message after a while to let the user know that the bot is still downloading the files and hasn't crashed."""
    while True:
        await asyncio.sleep(time)
        await call.reply(f"ℹ️ Il download di [c]{url}[/c] sta richiedendo più tempo del solito, ma è ancora in corso!")
        if not repeat:
            break


class PlayCommand(Command):
    command_name = "play"
    command_description = "Riproduce una canzone in chat vocale."
    command_syntax = "[ [guild] ] (url)"

    network_handlers = [PlayNH]

    @classmethod
    async def common(cls, call: Call):
        guild_name, url = call.args.match(r"(?:\[(.+)])?\s*<?(.+)>?")
        download_task = call.loop.create_task(call.net_request(Request("music_play", {"url": url, "guild_name": guild_name}), "discord"))
        notify_task = call.loop.create_task(notify_on_timeout(call, url, time=30, repeat=True))
        try:
            data: dict = await download_task
        finally:
            notify_task.cancel()
        for video in data["videos"]:
            if call.interface_name == "discord":
                # This is one of the unsafest things ever
                embed = pickle.loads(eval(video["discord_embed_pickle"]))
                await call.channel.send(content="✅ Aggiunto alla coda:", embed=embed)
            else:
                await call.reply(f"✅ [i]{video['title']}[/i] scaricato e aggiunto alla coda.")
