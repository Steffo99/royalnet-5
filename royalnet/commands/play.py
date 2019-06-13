import typing
import asyncio
import youtube_dl
import ffmpeg
import pickle
from ..utils import Command, Call, NetworkHandler, asyncify
from ..network import Request, ResponseSuccess
from ..error import TooManyFoundError, NoneFoundError
from ..audio import RoyalPCMAudio
if typing.TYPE_CHECKING:
    from ..bots import DiscordBot


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
            audio_sources: typing.List[RoyalPCMAudio] = await asyncify(RoyalPCMAudio.create_from_url, data["url"])
        else:
            audio_sources = await asyncify(RoyalPCMAudio.create_from_ytsearch, data["url"])
        await bot.add_to_music_data(audio_sources, guild)
        # Create response dictionary
        response = {
            "videos": [{
                "title": source.rpf.info.title,
                "discord_embed_pickle": str(pickle.dumps(source.rpf.info.to_discord_embed()))
            } for source in audio_sources]
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
        except Exception as exc:
            # RoyalPCMFile errors
            if isinstance(exc, FileExistsError):
                await call.reply(f"❌ Scaricare [c]{url}[/c] significherebbe sovrascrivere un file già esistente.\nQuesto è un bug, e non dovrebbe mai succedere. Se è appena successo, segnalate il problema a https://github.com/Steffo99/royalnet/issues.\n[p]{exc}[/p]")
                return
            # ffmpeg errors
            if isinstance(exc, ffmpeg.Error):
                await call.reply(f"⚠️ Errore durante la conversione a PCM di [c]{url}[/c]:\n[p]{exc}[/p]")
                return
            # youtube_dl errors
            if isinstance(exc, youtube_dl.utils.ContentTooShortError):
                await call.reply(f"⚠️ Mentre era in corso il download di [c]{url}[/c], la connessione è stata interrotta, quindi la riproduzione è stata annullata.\n[p]{exc}[/p]")
                return
            if isinstance(exc, youtube_dl.utils.UnavailableVideoError):
                await call.reply(f"⚠️ Non è disponibile nessun audio su [c]{url}[/c].\n[p]{exc}[/p]")
                return
            if isinstance(exc, youtube_dl.utils.SameFileError):
                await call.reply(f"❌ Scaricare [c]{url}[/c] significherebbe scaricare due file diversi sullo stesso nome.\nQuesto è un bug, e non dovrebbe mai succedere. Se è appena successo, segnalate il problema a https://github.com/Steffo99/royalnet/issues.\n[p]{exc}[/p]")
                return
            if isinstance(exc, youtube_dl.utils.GeoRestrictedError):
                await call.reply(f"⚠️ [c]{url}[/c] non può essere visualizzato nel paese in cui si trova il bot e non può essere scaricato.\n[p]{exc}[/p]")
                return
            if isinstance(exc, youtube_dl.utils.UnsupportedError):
                await call.reply(f"⚠️ [c]{url}[/c] non è supportato da YoutubeDL e non può essere scaricato.\n[p]{exc}[/p]")
                return
            if isinstance(exc, youtube_dl.utils.ExtractorError):
                await call.reply(f"⚠️ Errore nella ricerca di info per [c]{url}[/c]:\n[p]{exc}[/p]")
                return
            if isinstance(exc, youtube_dl.utils.DownloadError):
                await call.reply(f"⚠️ Errore nel download di [c]{url}[/c]:\n[p]{exc}[/p]")
                return
            if isinstance(exc, youtube_dl.utils.YoutubeDLError):
                await call.reply(f"⚠️ Errore di youtube_dl per [c]{url}[/c]:\n[p]{exc}[/p]")
                return
            raise
        finally:
            notify_task.cancel()
        for video in data["videos"]:
            if call.interface_name == "discord":
                # This is one of the unsafest things ever
                embed = pickle.loads(eval(video["discord_embed_pickle"]))
                await call.channel.send(content="✅ Aggiunto alla coda:", embed=embed)
            else:
                await call.reply(f"✅ [i]{video['title']}[/i] scaricato e aggiunto alla coda.")
