import random
import re
import discord
import discord.opus
import discord.voice_client
import functools
import sys
import db
import youtube_dl
import concurrent.futures
import platform
import typing
import os
import asyncio
import configparser
import subprocess
import async_timeout
import raven
import logging
import errors
import datetime

logging.basicConfig()

# Queue emojis
queue_emojis = [":one:",
                ":two:",
                ":three:",
                ":four:",
                ":five:",
                ":six:",
                ":seven:",
                ":eight:",
                ":nine:",
                ":keycap_ten:"]

# Init the event loop
loop = asyncio.get_event_loop()

# Init the config reader
config = configparser.ConfigParser()
config.read("config.ini")

# Radio messages
radio_messages = ["https://www.youtube.com/watch?v=3-yeK1Ck4yk"]
radio_messages_enabled = False
radio_message_in = int(config["Discord"]["radio_messages_every"])

# noinspection PyUnreachableCode
if __debug__:
    version = "discord-py-rewrite"
    commit_msg = "_Aggiornamento di Discordbot all'APIv6_"
else:
    # Find the latest git tag
    old_wd = os.getcwd()
    try:
        os.chdir(os.path.dirname(__file__))
        version = str(subprocess.check_output(["git", "describe", "--tags"]), encoding="utf8").strip()
        commit_msg = str(subprocess.check_output(["git", "log", "-1", "--pretty=%B"]), encoding="utf8").strip()
    except Exception:
        version = "❓"
    finally:
        os.chdir(old_wd)

# FFmpeg settings
ffmpeg_settings = {}


class DurationError(Exception):
    pass


class InfoNotRetrievedError(Exception):
    pass


class FileNotDownloadedError(Exception):
    pass


class AlreadyDownloadedError(Exception):
    pass


class InvalidConfigError(Exception):
    pass


class Video:
    def __init__(self, url: str=None, file: str=None, info: dict=None, enqueuer: discord.Member=None):
        self.url = url
        if file is None and info is None:
            self.file = str(hash(url)) + ".opus"
        elif info is not None:
            self.file = re.sub(r'[/\\?*"<>|!:]', "_", info["title"]) + ".opus"
        else:
            self.file = file
        self.downloaded = False if file is None else True
        self.info = info
        self.enqueuer = enqueuer

    def __str__(self):
        if self.info is None or "title" not in self.info:
            return f"`{self.file}`"
        return f"_{self.info['title']}_"

    def plain_text(self):
        if self.info is None or "title" not in self.info:
            return self.file
        return self.info['title']

    async def download(self, progress_hooks: typing.List["function"]=None):
        # File already downloaded
        if self.downloaded:
            raise AlreadyDownloadedError()
        # No progress hooks
        if progress_hooks is None:
            progress_hooks = []
        # Check if under max duration
        if self.info is not None and self.info.get("duration", 0) > int(config["YouTube"]["max_duration"]):
            raise DurationError()
        # Download the file
        with youtube_dl.YoutubeDL({"noplaylist": True,
                                   "format": "best",
                                   "postprocessors": [{
                                       "key": 'FFmpegExtractAudio',
                                       "preferredcodec": 'opus'
                                   }],
                                   "outtmpl": f"./opusfiles/{self.file}",
                                   "progress_hooks": progress_hooks,
                                   "quiet": True}) as ytdl:
            await loop.run_in_executor(executor, functools.partial(ytdl.download, [self.url]))
            self.downloaded = True

    def create_player(self) -> discord.PCMVolumeTransformer:
        # Check if the file has been downloaded
        if not self.downloaded:
            raise FileNotDownloadedError()
        return discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f"./opusfiles/{self.file}", **ffmpeg_settings))


class RoyalDiscordBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_channel: typing.Optional[discord.TextChannel] = None
        self.main_guild: typing.Optional[discord.Guild] = None

    async def on_ready(self):
        # Get the main channel
        self.main_channel = self.get_channel(int(config["Discord"]["main_channel"]))
        if not isinstance(self.main_channel, discord.TextChannel):
            raise InvalidConfigError("The main channel is not a TextChannel!")
        # Get the main guild
        self.main_guild = self.get_guild(int(config["Discord"]["server_id"]))
        if not isinstance(self.main_guild, discord.Guild):
            raise InvalidConfigError("The main guild does not exist!")
        await self.main_channel.send(f"ℹ Royal Bot avviato e pronto a ricevere comandi!\n"
                                     f"Ultimo aggiornamento: `{version}: {commit_msg}`")
        await self.change_presence(status=discord.Status.online, activity=None)

    async def on_message(self, message: discord.Message):
        if message.channel != self.main_channel or message.author.bot:
            return
        sentry.user_context({
            "discord": {
                "discord_id": message.author.id,
                "name": message.author.name,
                "discriminator": message.author.discriminator
            }
        })
        if not message.content.startswith("!"):
            await message.channel.send(f":warning: In questa chat sono consentiti solo comandi per il bot.\n"
                                       f"Riinvia il tuo messaggio in un altro canale!")
            await message.delete()
            return
        data = message.content.split(" ")
        if data[0] not in commands:
            await message.channel.send(":warning: Comando non riconosciuto.")
            return
        await commands[data[0]](channel=message.channel,
                                author=message.author,
                                params=data)

    async def on_error(self, event_method, *args, **kwargs):
        ei = sys.exc_info()
        print("ERRORE CRITICO:\n" + repr(ei[1]) + "\n\n" + repr(ei))
        try:
            await self.main_channel.send(f"☢️ **ERRORE CRITICO NELL'EVENTO** `{event_method}`\n"
                                         f"Il bot si è chiuso e si dovrebbe riavviare entro qualche minuto.\n"
                                         f"Una segnalazione di errore è stata automaticamente mandata a Steffo.\n\n"
                                         f"Dettagli dell'errore:\n"
                                         f"```python\n"
                                         f"{repr(ei[1])}\n"
                                         f"```")
            await self.change_presence(status=discord.Status.invisible)
            await self.close()
        except Exception as e:
            print("ERRORE CRITICO PIU' CRITICO:\n" + repr(e) + "\n\n" + repr(sys.exc_info()))
        loop.stop()
        sentry.captureException(exc_info=ei)
        exit(1)

    async def feed_pipe(self, connection):
        await self.wait_until_ready()
        while True:
            msg = await loop.run_in_executor(executor, connection.recv)
            if msg == "get cv":
                discord_members = list(self.main_guild.members)
                connection.send(discord_members)
            elif msg == "stop":
                await self.logout()
                exit(0)
            elif msg.startswith("!"):
                data = msg.split(" ")
                if data[0] not in commands:
                    connection.send("error")
                    continue
                await commands[data[0]](channel=self.get_channel(config["Discord"]["main_channel"]),
                                        author=None,
                                        params=data)
                connection.send("success")


# Init the executor
executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

# Init the Sentry client
sentry = raven.Client(config["Sentry"]["token"],
                      release=version,
                      install_logging_hook=False,
                      hook_libraries=[])


def command(func):
    """Decorator. Runs the function as a Discord command."""
    async def new_func(channel: discord.TextChannel, author: discord.Member, params: typing.List[str], *args, **kwargs):
        if author is not None:
            sentry.user_context({
                "discord_id": author.id,
                "username": f"{author.name}#{author.discriminator}"
            })
        else:
            sentry.user_context({
                "source": "Telegram"
            })
        try:
            result = await func(channel=channel, author=author, params=params, *args, **kwargs)
        except Exception:
            ei = sys.exc_info()
            try:
                await channel.send(f"☢ **ERRORE DURANTE L'ESECUZIONE DEL COMANDO {params[0]}**\n"
                                   f"Il comando è stato ignorato.\n"
                                   f"Una segnalazione di errore è stata automaticamente mandata a Steffo.\n\n"
                                   f"Dettagli dell'errore:\n"
                                   f"```python\n"
                                   f"{repr(ei[1])}\n"
                                   f"```")
            except Exception:
                pass
            sentry.captureException(exc_info=ei)
        else:
            return result
    return new_func


# def requires_voice_client(func):
#     "Decorator. Ensures the voice client is connected before running the command."
#     async def new_func(channel: discord.TextChannel, author: discord.Member, params: typing.List[str], *args, **kwargs):
#         global voice_client
#         if voice_client is None or not voice_client.is_connected():
#             await client.send_message(channel,
#                                       "⚠️ Non sono connesso alla cv!\n"
#                                       "Fammi entrare scrivendo `!cv` mentre sei in chat vocale.")
#             return
#         return await func(channel=channel, author=author, params=params, *args, **kwargs)
#     return new_func


def requires_rygdb(func, optional=False):
    async def new_func(channel: discord.TextChannel, author: discord.Member, params: typing.List[str], *args, **kwargs):
        session = db.Session()
        dbuser = await loop.run_in_executor(executor,
                                            session.query(db.Discord)
                                            .filter_by(discord_id=author.id)
                                            .join(db.Royal)
                                            .first)
        await loop.run_in_executor(executor, session.close)
        if not optional and dbuser is None:
            await channel.send("⚠️ Devi essere registrato su Royalnet per poter utilizzare questo comando.")
            return
        return await func(channel=channel, author=author, params=params, dbuser=dbuser, *args, **kwargs)
    return new_func


@command
async def cmd_ping(channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
    await channel.send(f"Pong!")


# @command
# async def cmd_cv(channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
#     if author is None:
#         await channel.send("⚠ Questo comando richiede un autore.")
#         return
#     if author.voice is None or author.voice.voice_channel is None:
#         await channel.send("⚠ Non sei in nessun canale!")
#         return
#     if voice_client is not None and voice_client.is_connected():
#         await voice_client.move_to(author.voice.voice_channel)
#     else:
#         voice_client = await client.join_voice_channel(author.voice.voice_channel)
#     await client.send_message(channel, f"✅ Mi sono connesso in <#{author.voice.voice_channel.id}>.")


# async def add_video_from_url(url, index: typing.Optional[int]=None, enqueuer: discord.Member=None):
#     # Retrieve info
#     with youtube_dl.YoutubeDL({"quiet": True,
#                                "ignoreerrors": True,
#                                "simulate": True}) as ytdl:
#         info = await loop.run_in_executor(executor,
#                                           functools.partial(ytdl.extract_info, url=url, download=False))
#     if info is None:
#         await client.send_message(client.get_channel(config["Discord"]["main_channel"]),
#                                   f"⚠ Non è stato trovato nessun video all'URL `{url}`,"
#                                   f" pertanto non è stato aggiunto alla coda.")
#         return
#     if "entries" in info:
#         # This is a playlist
#         for entry in info["entries"]:
#             if index is not None:
#                 voice_queue.insert(index, Video(url=entry["webpage_url"], info=entry, enqueuer=enqueuer))
#             else:
#                 voice_queue.append(Video(url=entry["webpage_url"], info=entry, enqueuer=enqueuer))
#         return
#     # This is a single video
#     if index is not None:
#         voice_queue.insert(index, Video(url=url, info=info, enqueuer=enqueuer))
#     else:
#         voice_queue.append(Video(url=url, info=info, enqueuer=enqueuer))


# async def add_video_from_file(file, index: typing.Optional[int]=None, enqueuer: discord.Member=None):
#     if index is not None:
#         voice_queue.insert(index, Video(file=file, enqueuer=enqueuer))
#     else:
#         voice_queue.append(Video(file=file, enqueuer=enqueuer))


# @command
# @requires_voice_client
# async def cmd_play(channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
#     if len(params) < 2:
#         await client.send_message(channel, "⚠ Non hai specificato una canzone da riprodurre!\n"
#                                            "Sintassi: `!play <url|ricercayoutube|nomefile>`")
#         return
#     # If the radio messages are enabled...
#     global radio_messages_enabled
#     if radio_messages_enabled:
#         global radio_message_in
#         radio_message_in -= 1
#         if radio_message_in <= 0:
#             radio_message = random.sample(radio_messages, 1)[0]
#             radio_message_in = int(config["Discord"]["radio_messages_every"])
#             await add_video_from_url(radio_message)
#             await client.send_message(channel, f"✅ Aggiunto un messaggio radio, disattiva con `!radiomessages off`.")
#     # Parse the parameter as URL
#     url = re.match(r"(?:https?://|ytsearch[0-9]*:).*", " ".join(params[1:]).strip("<>"))
#     if url is not None:
#         # This is a url
#         await add_video_from_url(url.group(0), enqueuer=author)
#         await client.send_message(channel, f"✅ Video aggiunto alla coda.")
#         return
#     # Parse the parameter as file
#     file_path = os.path.join(os.path.join(os.path.curdir, "opusfiles"), " ".join(params[1:]))
#     if os.path.exists(file_path):
#         # This is a file
#         await add_video_from_file(file=file_path, enqueuer=author)
#         await client.send_message(channel, f"✅ Video aggiunto alla coda.")
#         return
#     file_path += ".opus"
#     if os.path.exists(file_path):
#         # This is a file
#         await add_video_from_file(file=file_path, enqueuer=author)
#         await client.send_message(channel, f"✅ Video aggiunto alla coda.")
#         return
#     # Search the parameter on youtube
#     search = " ".join(params[1:])
#     # This is a search
#     await add_video_from_url(url=f"ytsearch:{search}", enqueuer=author)
#     await client.send_message(channel, f"✅ Video aggiunto alla coda.")


# @command
# @requires_voice_client
# async def cmd_skip(channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
#     global voice_player
#     if voice_player is None:
#         await client.send_message(channel, "⚠ Non c'è nessun video in riproduzione.")
#         return
#     voice_player.stop()
#     await client.send_message(channel, f"⏩ Video saltato.")


# @command
# @requires_voice_client
# async def cmd_remove(channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
#     if len(voice_queue) == 0:
#         await client.send_message(channel, "⚠ Non c'è nessun video in coda.")
#         return
#     if len(params) == 1:
#         index = len(voice_queue) - 1
#     else:
#         try:
#             index = int(params[1]) - 1
#         except ValueError:
#             await client.send_message(channel, "⚠ Il numero inserito non è valido.\n"
#                                       "Sintassi: `!remove [numerovideoiniziale] [numerovideofinale]`")
#             return
#     if len(params) < 3:
#         if abs(index) >= len(voice_queue):
#             await client.send_message(channel, "⚠ Il numero inserito non corrisponde a nessun video nella playlist.\n"
#                                       "Sintassi: `!remove [numerovideoiniziale] [numerovideofinale]`")
#             return
#         video = voice_queue.pop(index)
#         await client.send_message(channel, f":regional_indicator_x: {str(video)} è stato rimosso dalla coda.")
#         return
#     try:
#         start = int(params[1]) - 1
#     except ValueError:
#         await client.send_message(channel, "⚠ Il numero iniziale inserito non è valido.\n"
#                                   "Sintassi: `!remove [numerovideoiniziale] [numerovideofinale]`")
#         return
#     if start >= len(voice_queue):
#         await client.send_message(channel, "⚠ Il numero iniziale inserito non corrisponde a nessun video nella"
#                                            " playlist.\n"
#                                   "Sintassi: `!remove [numerovideoiniziale] [numerovideofinale]`")
#         return
#     try:
#         end = int(params[2]) - 2
#     except ValueError:
#         await client.send_message(channel, "⚠ Il numero finale inserito non è valido.\n"
#                                   "Sintassi: `!remove [numerovideoiniziale] [numerovideofinale]`")
#         return
#     if end >= len(voice_queue):
#         await client.send_message(channel, "⚠ Il numero finale inserito non corrisponde a nessun video nella"
#                                            " playlist.\n"
#                                   "Sintassi: `!remove [numerovideoiniziale] [numerovideofinale]`")
#         return
#     if start > end:
#         await client.send_message(channel, "⚠ Il numero iniziale è maggiore del numero finale.\n"
#                                   "Sintassi: `!remove [numerovideoiniziale] [numerovideofinale]`")
#         return
#     del voice_queue[start:end]
#     await client.send_message(channel, f":regional_indicator_x: {end - start} video rimossi dalla coda.")


# @command
# async def cmd_queue(channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
#     if len(voice_queue) == 0:
#         await client.send_message(channel, "**Video in coda:**\n"
#                                            "nessuno")
#         return
#     msg = "**Video in coda:**\n"
#     for index, video in enumerate(voice_queue[:10]):
#         msg += f"{queue_emojis[index]} {str(video)}\n"
#     if len(voice_queue) > 10:
#         msg += f"più altri {len(voice_queue) - 10} video!"
#     await client.send_message(channel, msg)


# @command
# @requires_voice_client
# async def cmd_shuffle(channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
#     if len(voice_queue) == 0:
#         await client.send_message(channel, "⚠ Non ci sono video in coda!")
#         return
#     random.shuffle(voice_queue)
#     await client.send_message(channel, "♠️ ♦️ ♣️ ♥️ Shuffle completo!")


# @command
# @requires_voice_client
# async def cmd_clear(channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
#     global voice_queue
#     if len(voice_queue) == 0:
#         await client.send_message(channel, "⚠ Non ci sono video in coda!")
#         return
#     voice_queue = []
#     await client.send_message(channel, ":regional_indicator_x: Tutti i video in coda rimossi.")


# @command
# @requires_voice_client
# async def cmd_dump_voice_player_error(channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
#     global voice_player
#     if voice_player is None:
#         return
#     await client.send_message(channel, f"```\n{str(voice_player.error)}\n```")


@command
async def cmd_register(channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
    session = db.Session()
    if len(params) < 1:
        await channel.send("⚠️ Non hai specificato un username!\n"
                           "Sintassi corretta: `!register <username_ryg>`")
        return
    try:
        # noinspection PyTypeChecker
        d = db.Discord.create(session,
                              royal_username=params[0],
                              discord_user=author)
    except errors.AlreadyExistingError:
        await channel.send("⚠ Il tuo account Discord è già collegato a un account RYG "
                           "o l'account RYG che hai specificato è già collegato a un account Discord.")
        return
    session.add(d)
    session.commit()
    session.close()
    await channel.send("✅ Sincronizzazione completata!")


# @command
# @requires_voice_client
# async def cmd_forceplay(channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
#     if voice_player is not None:
#         voice_player.stop()
#     if len(params) < 2:
#         await client.send_message(channel, "⚠ Non hai specificato una canzone da riprodurre!\n"
#                                            "Sintassi: `!forceplay <url|ricercayoutube|nomefile>`")
#         return
#     # Parse the parameter as URL
#     url = re.match(r"(?:https?://|ytsearch[0-9]*:).*", " ".join(params[1:]).strip("<>"))
#     if url is not None:
#         # This is a url
#         await add_video_from_url(url.group(0), enqueuer=author, index=0)
#         await client.send_message(channel, f"✅ Riproduzione del video forzata.")
#         return
#     # Parse the parameter as file
#     file_path = os.path.join(os.path.join(os.path.curdir, "opusfiles"), " ".join(params[1:]))
#     if os.path.exists(file_path):
#         # This is a file
#         await add_video_from_file(file=file_path, enqueuer=author, index=0)
#         await client.send_message(channel, f"✅ Riproduzione del video forzata.")
#         return
#     file_path += ".opus"
#     if os.path.exists(file_path):
#         # This is a file
#         await add_video_from_file(file=file_path, enqueuer=author, index=0)
#         await client.send_message(channel, f"✅ Riproduzione del video forzata.")
#         return
#     # Search the parameter on youtube
#     search = " ".join(params[1:])
#     # This is a search
#     await add_video_from_url(url=f"ytsearch:{search}", enqueuer=author, index=0)
#     await client.send_message(channel, f"✅ Riproduzione del video forzata.")


# @command
# async def cmd_radiomessages(channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
#     global radio_messages_enabled
#     if len(params) < 2:
#         radio_messages_enabled = not radio_messages_enabled
#     else:
#         if params[1].lower() == "on":
#             radio_messages_enabled = True
#         elif params[1].lower() == "off":
#             radio_messages_enabled = False
#         else:
#             await client.send_message(channel, "⚠ Sintassi del comando non valida.\n"
#                                                "Sintassi: `!radiomessages [on|off]`")
#             return
#     await client.send_message(channel,
#                              f"📻 Messaggi radio **{'attivati' if radio_messages_enabled else 'disattivati'}**.")


# async def queue_predownload_videos():
#     while True:
#         for index, video in enumerate(voice_queue[:int(config["YouTube"]["predownload_videos"])].copy()):
#             if video.downloaded:
#                 continue
#             try:
#                 with async_timeout.timeout(int(config["YouTube"]["download_timeout"])):
#                     await video.download()
#             except asyncio.TimeoutError:
#                 await client.send_message(client.get_channel(config["Discord"]["main_channel"]),
#                                           f"⚠️ Il download di {str(video)} ha richiesto più di"
#                                           f" {config['YouTube']['download_timeout']} secondi, pertanto è stato rimosso"
#                                           f" dalla coda.")
#                 del voice_queue[index]
#                 continue
#             except DurationError:
#                 await client.send_message(client.get_channel(config["Discord"]["main_channel"]),
#                                           f"⚠️ {str(video)} dura più di"
#                                           f" {str(int(config['YouTube']['max_duration']) // 60)}"
#                                           f" minuti, quindi è stato rimosso dalla coda.")
#                 del voice_queue[index]
#                 continue
#             except Exception as e:
#                 await client.send_message(client.get_channel(config["Discord"]["main_channel"]),
#                                           f"⚠️ E' stato incontrato un errore durante il download di {str(video)},"
#                                           f" quindi è stato rimosso dalla coda.\n\n"
#                                           f"```python\n"
#                                           f"{str(e)}"
#                                           f"```")
#                 del voice_queue[index]
#                 continue
#         await asyncio.sleep(1)


song_special_messages = {
    "despacito": ":arrow_forward: this is so sad. alexa play {song}",
    "faded": ":arrow_forward: Basta Garf, lasciami ascoltare {song}",
    "ligma": ":arrow_forward: What is ligma? {song}!",
    "sugma": ":arrow_forward: What is sugma? {song}!",
    "sugondese": ":arrow_forward: What is sugondese? {song}!",
    "bofa": ":arrow_forward: What is bofa? {song}!",
    "updog": ":arrow_forward: What is updog? {song}!",
    "sayo-nara": ":arrow_forward: I gently open the door. {song} awaits me inside.",
    "monika": ":arrow_forward: Just Monika. Just Monika. Just {song}.",
    "take me home": ":arrow_forward: Take me home, to {song}, the place I belong!",
    "never gonna give you up": ":arrow_forward: Rickrolling in 2018. Enjoy {song}!",
    "september": ":arrow_forward: Do you remember? {song}.",
    "homestuck": ":arrow_forward: > Enter song name. {song}",
    "undertale": ":arrow_forward: Howdy! I'm Flowey! Listen to this friendly song: {song}",
    "pumped up kicks": ":arrow_forward: Non metterti mica in testa strane idee ascoltando {song}...",
    "jesus": ":arrow_forward: Respawn in 3 giorni. Intanto, ascolta {song}.",
    "through The fire And flames": ":arrow_forward: Fai {song} su osu!, se ne sei capace!",
    "slow clap": ":arrow_forward: :clap: :clap: :clap: {song} :clap: :clap: :clap:",
    "pub scrubs": ":arrow_forward: MAV COME BACK WE MISS {song}!",
    "alleluia": ":arrow_forward: Wah. Waaaah. Waluigi tiime: {song}",
    "wah": ":arrow_forward: Wah. Waaaah. Waluigi tiime: {song}",
    "waluigi": ":arrow_forward: Wah. Waaaah. Waluigi tiime: {song}",
    "nyan cat": ":arrow_forward: Meow! :3 {song}",
    "dragonborn": ":arrow_forward: FUS RO {song}!",
    "dovahkiin": ":arrow_forward: FUS RO {song}!",
    "initial d": ":arrow_forward: Guarda mamma sto driftando sul balcone di Balu grazie a {song}!",
    "persona": ":arrow_forward: You'll never see {song} comiiiiing!",
    "flamingo": ":arrow_forward: How many {song} do you have to eat?",
    "linkin park": ":arrow_forward: Crawling in my {song}!",
    "magicite": "⚠️ Warning: {song} contiene numerosi bug.",
    "papers please": ":arrow_forward: Glory to Arstotzka! {song}!",
    "we are number one": ":arrow_forward: Now paying respect to Robbie Rotten: {song}",
    "jump up superstar": ":arrow_forward: Is {song} the Tengen Toppa Guren Lagann opening?"
}


# async def queue_play_next_video():
#     await client.wait_until_ready()
#     global voice_client
#     global voice_player
#     global now_playing
#     while True:
#         if voice_client is None:
#             await asyncio.sleep(1)
#             continue
#         if voice_player is not None and not voice_player.is_done():
#             await asyncio.sleep(0.5)
#             continue
#         if len(voice_queue) == 0:
#             await asyncio.sleep(0.5)
#             if now_playing is not None:
#                 await client.change_presence()
#                 now_playing = None
#             continue
#         now_playing = voice_queue[0]
#         if not now_playing.downloaded:
#             await asyncio.sleep(0.5)
#             continue
#         voice_player = await now_playing.create_player()
#         voice_player.start()
#         if now_playing.enqueuer is not None:
#             session = db.Session()
#             enqueuer = await loop.run_in_executor(executor, session.query(db.Discord).filter_by(discord_id=now_playing.enqueuer.id).one_or_none)
#             played_music = db.PlayedMusic(enqueuer=enqueuer,
#                                           filename=now_playing.plain_text(),
#                                           timestamp=datetime.datetime.now())
#             session.add(played_music)
#             await loop.run_in_executor(executor, session.commit)
#             await loop.run_in_executor(executor, session.close)
#         await client.change_presence(game=discord.Game(name=now_playing.plain_text(), type=2))
#         for key in song_special_messages:
#             if key in now_playing.file.lower():
#                 await client.send_message(client.get_channel(config["Discord"]["main_channel"]),
#                                           song_special_messages[key].format(song=str(now_playing)))
#                 break
#         else:
#             await client.send_message(client.get_channel(config["Discord"]["main_channel"]),
#                                       f":arrow_forward: Ora in riproduzione: {str(now_playing)}")
#         del voice_queue[0]


commands = {
    "!ping": cmd_ping,
    # "!cv": cmd_cv,
    # "!summon": cmd_cv,
    # "!play": cmd_play,
    # "!p": cmd_play,
    # "!search": cmd_play,
    # "!file": cmd_play,
    # "!skip": cmd_skip,
    # "!s": cmd_skip,
    # "!remove": cmd_remove,
    # "!cancel": cmd_remove,
    # "!queue": cmd_queue,
    # "!q": cmd_queue,
    # "!shuffle": cmd_shuffle,
    # "!clear": cmd_clear,
    # "!dump_vp": cmd_dump_voice_player_error,
    "!register": cmd_register,
    # "!forceplay": cmd_forceplay,
    # "!fp": cmd_forceplay,
    # "!radiomessages": cmd_radiomessages
}


def process(users_connection=None):
    print("[Discord] Preparing...")
    bot = RoyalDiscordBot()
    if users_connection is not None:
        asyncio.ensure_future(bot.feed_pipe(users_connection))
    # asyncio.ensure_future(queue_predownload_videos())
    # asyncio.ensure_future(queue_play_next_video())
    loop.run_until_complete(bot.login(config["Discord"]["bot_token"], bot=True))
    print("[Discord] Logged in successfully!")
    loop.run_until_complete(bot.connect())


if __name__ == "__main__":
    process()
