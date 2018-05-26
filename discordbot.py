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
import stagismo
import platform
import typing
import os
import asyncio
import configparser
import subprocess
import async_timeout
import raven
import cast

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

class DurationError(Exception):
    pass

class LocalFileError(Exception):
    pass


class OldVideo:
    def __init__(self):
        self.enqueuer = None  # type: typing.Optional[discord.User]
        self.filename = None  # type: typing.Optional[str]
        self.ytdl_url = None  # type: typing.Optional[str]
        self.data = None      # type: typing.Optional[dict]

    @staticmethod
    async def init(user_id: str, *, filename=None, ytdl_url=None, data=None):
        if filename is None and ytdl_url is None:
            raise Exception("Filename or url must be specified")
        self = OldVideo()
        self.enqueuer = int(user_id)
        self.filename = filename
        self.ytdl_url = ytdl_url
        self.data = data if data is not None else {}
        return self

    async def download(self):
        # Retrieve info before downloading
        with youtube_dl.YoutubeDL() as ytdl:
            info = await loop.run_in_executor(executor, functools.partial(ytdl.extract_info, self.ytdl_url, download=False))
        if "entries" in info:
            info = info["entries"][0]
        file_id = info.get("title", str(hash(self.ytdl_url)))
        file_id = re.sub(r'[/\\?*"<>|]', "_", file_id)
        # Set the filename to the downloaded video
        self.filename = file_id
        if os.path.exists(f"opusfiles/{file_id}.opus"):
            return
        if info.get("duration", 1) > int(config["YouTube"]["max_duration"]):
            raise DurationError(f"File duration is over the limit "
                                f"set in the config ({config['YouTube']['max_duration']}).")
        ytdl_args = {"noplaylist": True,
                     "format": "best",
                     "postprocessors": [{
                         "key": 'FFmpegExtractAudio',
                         "preferredcodec": 'opus'
                     }],
                     "outtmpl": f"opusfiles/{file_id}.opus",
                     "quiet": True}
        if "youtu" in self.ytdl_url:
            ytdl_args["username"] = config["YouTube"]["username"]
            ytdl_args["password"] = config["YouTube"]["password"]
        # Download the video
        with youtube_dl.YoutubeDL(ytdl_args) as ytdl:
            await loop.run_in_executor(executor, functools.partial(ytdl.download, [self.ytdl_url]))

    async def add_to_db(self):
        session = await loop.run_in_executor(executor, db.Session)
        pm = db.PlayedMusic(enqueuer_id=self.enqueuer,
                            filename=self.filename)
        session.add(pm)
        await loop.run_in_executor(executor, session.commit)
        await loop.run_in_executor(executor, session.close)

    def __str__(self):
        if self.data.get("title") is not None:
            return f"{self.data.get('title')}"
        elif self.filename is not None:
            return f"`{self.filename}`"
        else:
            return f"<{self.ytdl_url}>"


class Video:
    def __init__(self, url=None, file=None):
        self.url = url
        self.file = file

    def __str__(self):
        pass

    async def retrieve_info(self):
        if url is None:
            raise LocalFileError()
        with youtube_dl.YoutubeDL({"quiet": True,
                                   "ignoreerrors": True,
                                   "simulate": True}) as ytdl:
            await loop.run_in_executor(executor, functools.partial(ytdl.extract_info, url=self.url, download=False)
            # TODO


if __debug__:
    version = "Dev"
    commit_msg = "_in sviluppo_"
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

# Init the discord bot
client = discord.Client()
if platform.system() == "Linux":
    discord.opus.load_opus("/usr/lib/x86_64-linux-gnu/libopus.so")
elif platform.system() == "Windows":
    discord.opus.load_opus("libopus-0.dll")

voice_client: typing.Optional[discord.VoiceClient] = None
voice_player: typing.Optional[discord.voice_client.StreamPlayer] = None
voice_queue: typing.List[OldVideo] = []

# Init the executor
executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

# Init the Sentry client
sentry = raven.Client(config["Sentry"]["token"],
                      release=version,
                      install_logging_hook=False,
                      hook_libraries=[])


async def on_error(event, *args, **kwargs):
    ei = sys.exc_info()
    print("ERRORE CRITICO:\n" + repr(ei[1]) + "\n\n" + repr(ei))
    try:
        await client.send_message(client.get_channel(config["Discord"]["main_channel"]),
                                  f"☢️ **ERRORE CRITICO NELL'EVENTO** `{event}`\n"
                                  f"Il bot si è chiuso e si dovrebbe riavviare entro qualche minuto.\n"
                                  f"Una segnalazione di errore è stata automaticamente mandata a Steffo.\n\n"
                                  f"Dettagli dell'errore:\n"
                                  f"```python\n"
                                  f"{repr(ei[1])}\n"
                                  f"```")
        if voice_client is not None:
            await voice_client.disconnect()
        await client.change_presence(status=discord.Status.invisible)
        await client.close()
    except Exception as e:
        print("ERRORE CRITICO PIU' CRITICO:\n" + repr(e) + "\n\n" + repr(sys.exc_info()))
    loop.stop()
    sentry.captureException(exc_info=ei)
    os._exit(1)
    pass


@client.event
async def on_ready():
    await client.send_message(client.get_channel(config["Discord"]["main_channel"]),
                              f"ℹ Royal Bot avviato e pronto a ricevere comandi!\n"
                              f"Ultimo aggiornamento: `{version}: {commit_msg}`")
    await client.change_presence(game=None, status=discord.Status.online)


@client.event
async def on_message(message: discord.Message):
    global voice_queue
    global voice_player
    if not message.content.startswith("!"):
        return
    sentry.user_context({
        "discord": {
            "discord_id": message.author.id,
            "name": message.author.name,
            "discriminator": message.author.discriminator
        }
    })
    await client.send_typing(message.channel)
    session = await loop.run_in_executor(executor, db.Session)
    user = session.query(db.Discord).filter_by(discord_id=message.author.id).one_or_none()
    if user is None:
        user = db.Discord(discord_id=message.author.id,
                          name=message.author.name,
                          discriminator=message.author.discriminator,
                          avatar_hex=message.author.avatar)
        session.add(user)
        await loop.run_in_executor(executor, session.commit)
    else:
        sentry.user_context({
            "discord": {
                "discord_id": message.author.id,
                "name": message.author.name,
                "discriminator": message.author.discriminator
            },
            "royal": {
                "user_id": user.royal_id
            }
        })
    if message.content.startswith("!ping"):
        await cmd_ping(channel=message.channel,
                       author=message.author,
                       params=["/ping"])
    elif message.content.startswith("!link"):
        if user.royal_id is None:
            await client.send_message(message.channel,
                                      "⚠️ Il tuo account Discord è già collegato a un account RYG "
                                      "o l'account RYG che hai specificato è già collegato a un account Discord.")
            return
        try:
            username = message.content.split(" ", 1)[1]
        except IndexError:
            await client.send_message(message.channel, "⚠️ Non hai specificato un username!\n"
                                                       "Sintassi corretta: `!link <username_ryg>`")
            return
        royal = session.query(db.Royal).filter_by(username=username).one_or_none()
        if royal is None:
            await client.send_message(message.channel,
                                      "⚠️ Non esiste nessun account RYG con questo nome.")
            return
        user.royal_id = royal.id
        session.commit()
        session.close()
        await client.send_message(message.channel, "✅ Sincronizzazione completata!")
    elif message.content.startswith("!cv"):
        cmd_cv(channel=message.channel,
               author=message.author,
               params=message.content.split(" "))
    elif message.content.startswith("!play"):
        # Find the sent url
        try:
            url = message.content.split(" ", 1)[1]
        except IndexError:
            await client.send_message(message.channel, "⚠️ Non hai specificato un url!\n"
                                                       "Sintassi corretta: `!play <video>`")
            return
        if "playlist" in url:
            # If target is a playlist
            await client.send_message(message.channel,
                                      f"ℹ️ Il link che hai inviato contiene una playlist.\n"
                                      f"L'elaborazione delle playlist solitamente richiede molto tempo.")
            with youtube_dl.YoutubeDL({"quiet": True,
                                       "ignoreerrors": True,
                                       "simulate": True}) as ytdl:
                playlist_data = await loop.run_in_executor(executor,
                                                           functools.partial(ytdl.extract_info, url, download=False))
            for entry in playlist_data["entries"]:
                # Ignore empty videos
                if entry is None:
                    continue
                # Add the video to the queue
                video = await OldVideo.init(user_id=message.author.id, ytdl_url=entry["webpage_url"], data=entry)
                voice_queue.append(video)
            await client.send_message(message.channel,
                                      f"✅ Aggiunti alla coda **{len(playlist_data['entries']) } video**.")
        else:
            # If target is a single video
            video = await OldVideo.init(user_id=message.author.id, ytdl_url=url)
            await client.send_message(message.channel, f"✅ Aggiunto alla coda: {str(video)}")
            voice_queue.append(video)
    elif message.content.startswith("!search"):
        await client.send_typing(message.channel)
        # The bot should be in voice chat
        if voice_client is None:
            await client.send_message(message.channel, "⚠️ Non sono connesso alla cv!\n"
                                                       "Fammi entrare scrivendo `!cv` mentre sei in chat vocale.")
            return
        # Find the sent text
        try:
            text = message.content.split(" ", 1)[1]
        except IndexError:
            await client.send_message(message.channel, "⚠️ Non hai specificato il titolo!\n"
                                                       "Sintassi corretta: `!search <titolo>`")
            return
        # If target is a single video
        video = await OldVideo.init(user_id=message.author.id, ytdl_url=f"ytsearch:{text}")
        await client.send_message(message.channel, f"✅ Aggiunto alla coda: {str(video)}")
        voice_queue.append(video)
    elif message.content.startswith("!file"):
        await client.send_typing(message.channel)
        # The bot should be in voice chat
        if voice_client is None:
            await client.send_message(message.channel, "⚠️ Non sono connesso alla cv!\n"
                                                       "Fammi entrare scrivendo `!cv` mentre sei in chat vocale.")
            return
        # Find the sent text
        try:
            text: str = message.content.split(" ", 1)[1]
        except IndexError:
            await client.send_message(message.channel, "⚠️ Non hai specificato il nome del file!\n"
                                                       "Sintassi corretta: `!file <nomefile>`")
            return
        # If target is a single video
        video = await OldVideo.init(user_id=message.author.id, filename=text)
        await client.send_message(message.channel, f"✅ Aggiunto alla coda: {str(video)}")
        voice_queue.append(video)
    elif message.content.startswith("!skip"):
        global voice_player
        voice_player.stop()
        await client.send_message(message.channel, f"⏩ Video saltato.")
    elif message.content.startswith("!pause"):
        if voice_player is None or not voice_player.is_playing():
            await client.send_message(message.channel, f"⚠️ Non è in corso la riproduzione di un video, "
                                                       f"pertanto non c'è niente da pausare.")
            return
        voice_player.pause()
        await client.send_message(message.channel, f"⏸ Riproduzione messa in pausa.\n"
                                                   f"Riprendi con `!resume`.")
    elif message.content.startswith("!resume"):
        if voice_player is None or voice_player.is_playing():
            await client.send_message(message.channel, f"⚠️ Non c'è nulla in pausa da riprendere!")
            return
        voice_player.resume()
        await client.send_message(message.channel, f"▶️ Riproduzione ripresa.")
    elif message.content.startswith("!cancel"):
        if not len(voice_queue) > 0:
            await client.send_message(message.channel, f"⚠ Non ci sono video da annullare.")
            return
        voice_queue.pop()
        await client.send_message(message.channel, f"❌ L'ultimo video aggiunto alla playlist è stato rimosso.")
    elif message.content.startswith("!stop"):
        if voice_player is None:
            await client.send_message(message.channel, f"⚠ Non c'è nulla da interrompere!")
            return
        voice_queue = []
        voice_player.stop()
        voice_player = None
        await client.send_message(message.channel, f"⏹ Riproduzione interrotta e playlist svuotata.")
    elif message.content.startswith("!disconnect"):
        if voice_client is None:
            await client.send_message(message.channel, "⚠ Il bot in questo momento non è in chat vocale.")
            return
        if voice_player is not None:
            await client.send_message(message.channel, "⚠ Prima di disconnettere il bot, interrompi la riproduzione di "
                                                       "una canzone scrivendo `!stop`.")
            return
        await voice_client.disconnect()
        voice_client = None
        await client.send_message(message.channel, "✅ Mi sono disconnesso dalla chat vocale.")
    elif message.content.startswith("!queue"):
        msg = "**Video in coda:**\n"
        for position, video in enumerate(voice_queue[:10]):
            msg += f"{queue_emojis[position]} {str(voice_queue[position])}\n"
        if len(voice_queue) > 10:
            msg += f"e altri {len(voice_queue) - 10} video!\n"
        await client.send_message(message.channel, msg)
    elif message.content.startswith("!cast"):
        try:
            spell = message.content.split(" ", 1)[1]
        except IndexError:
            await client.send_message(message.channel, "⚠️ Non hai specificato nessun incantesimo!\n"
                                                       "Sintassi corretta: `!cast <nome_incantesimo>`")
            return
        target: discord.Member = random.sample(list(message.server.members), 1)[0]
        await client.send_message(message.channel, cast.cast(spell_name=spell, target_name=target.name,
                                                             platform="discord"))
    elif message.content.startswith("!smecds"):
        ds = random.sample(stagismo.listona, 1)[0]
        await client.send_message(message.channel, f"Secondo me, è colpa {ds}.", tts=True)
    elif __debug__ and message.content.startswith("!exception"):
        raise Exception("!exception was called")


async def update_users_pipe(users_connection):
    await client.wait_until_ready()
    while True:
        msg = await loop.run_in_executor(executor, users_connection.recv)
        if msg == "/cv":
            discord_members = list(client.get_server(config["Discord"]["server_id"]).members)
            users_connection.send(discord_members)


def command(func):
    """Decorator. Runs the function as a Discord command."""
    async def new_func(channel: discord.Channel, author: discord.Member, params: typing.List[str], *args, **kwargs):
        sentry.user_context({
            "discord_id": author.id,
            "username": f"{author.name}#{author.discriminator}"
        })
        try:
            result = await func(channel=channel, author=author, params=params, *args, **kwargs)
        except Exception:
            try:
                await client.send_message(channel,
                                          f"☢ **ERRORE DURANTE L'ESECUZIONE DEL COMANDO {params[0]}**\n"
                                          f"Il comando è stato ignorato.\n"
                                          f"Una segnalazione di errore è stata automaticamente mandata a Steffo.\n\n"
                                          f"Dettagli dell'errore:\n"
                                          f"```python\n"
                                          f"{repr(ei[1])}\n"
                                          f"```")
            except Exception:
                pass
            ei = sys.exc_info()
            sentry.captureException(exc_info=ei)
        else:
            return result
    return new_func


def requires_cv(func):
    "Decorator. Ensures the voice client is connected before running the command."
    async def new_func(channel: discord.Channel, author: discord.User, params: typing.List[str], *args, **kwargs):
        global voice_client
        if voice_client is None or not voice_client.is_connected():
            await client.send_message(channel,
                                      "⚠️ Non sono connesso alla cv!\n"
                                      "Fammi entrare scrivendo `!cv` mentre sei in chat vocale.")
            return
        return await func(channel=channel, author=author, params=params, *args, **kwargs)
    return new_func


def requires_rygdb(func, optional=False):
    async def new_func(channel: discord.Channel, author: discord.Member, params: typing.List[str], *args, **kwargs):
        session = await loop.run_in_executor(executor, db.Session)
        dbuser = await loop.run_in_executor(executor,
                                            session.query(db.Discord)
                                            .filter_by(discord_id=author.id)
                                            .join(db.Royal)
                                            .first)
        if not optional and dbuser is None:
            await client.send_message(channel,
                                      "⚠️ Devi essere registrato su Royalnet per poter utilizzare questo comando.")
            return
        await loop.run_in_executor(executor, session.close)
        return await func(channel=channel, author=author, params=params, dbuser=dbuser, *args, **kwargs)
    return new_func


@command
async def cmd_ping(channel: discord.Channel, author: discord.Member, params: typing.List[str]):
    await client.send_message(channel, f"Pong!")


@command
async def cmd_cv(channel: discord.Channel, author: discord.Member, params: typing.List[str]):
    await client.send_typing(channel)
    if author.voice.voice_channel is None:
        await client.send_message(channel, "⚠ Non sei in nessun canale!")
        return
    global voice_client
    if voice_client is not None and voice_client.is_connected():
        await voice_client.move_to(author.voice.voice_channel)
    else:
        voice_client = await client.join_voice_channel(author.voice.voice_channel)
    await client.send_message(channel, f"✅ Mi sono connesso in <#{author.voice.voice_channel.id}>.")


@command
@requires_cv
async def cmd_play(channel: discord.Channel, author: discord.Member, params: typing.List[str]):
    if len(params) < 2:
        await client.send_message(channel, "⚠ Non hai specificato una canzone da riprodurre!\n"
                                           "Sintassi: `!play <url|ricercayoutube|nomefile>`")
        return
    # Parse the parameter as URL
    url = re.match(r"(?:https?://|ytsearch[0-9]*:).*", params[1].strip("<>"))
    if url.group(0) is not None:
        # This is a url
        return
    # Parse the parameter as file
    file_path = os.path.join(os.path.join(os.path.curdir, "opusfiles"), params[1])
    if os.path.exists(file_path):
        # This is a file
        return
    # Search the parameter on youtube
    search = params[1]
    # This is a search
    return


async def update_music_queue():
    await client.wait_until_ready()
    global voice_client
    global voice_player
    global voice_queue
    while True:
        try:
            if voice_client is None:
                await asyncio.sleep(5)
                continue
            if voice_player is not None and not voice_player.is_done():
                await asyncio.sleep(1)
                continue
            if len(voice_queue) == 0:
                await client.change_presence()
                await asyncio.sleep(1)
                continue
            video = voice_queue.pop(0)
            if video.ytdl_url:
                await client.send_message(client.get_channel(config["Discord"]["main_channel"]),
                                          f"⬇️ E' iniziato il download di {str(video)}.")
                try:
                    async with async_timeout.timeout(30):
                        await video.download()
                except asyncio.TimeoutError:
                    await client.send_message(client.get_channel(config["Discord"]["main_channel"]),
                                              f"⚠️ Il download della canzone ha richiesto più di 30 secondi ed è stato "
                                              f"annullato. ")
                    continue
                except DurationError:
                    await client.send_message(client.get_channel(config["Discord"]["main_channel"]),
                                              f"⚠️ Il file supera il limite di durata impostato in config.ini "
                                              f"(`{config['YouTube']['max_duration']}` secondi).")
                    continue
                except Exception as e:
                    await client.send_message(client.get_channel(config["Discord"]["main_channel"]),
                                              f"⚠️ C'è stato un errore durante il download di `{video.ytdl_url}`:\n"
                                              f"```\n"
                                              f"{e}\n"
                                              f"```")
                    continue
            voice_player = voice_client.create_ffmpeg_player(f"opusfiles/{video.filename}.opus")
            voice_player.start()
            await client.send_message(client.get_channel(config["Discord"]["main_channel"]),
                                      f"▶ Ora in riproduzione in <#{voice_client.channel.id}>:\n"
                                      f"`{video.filename}`")
            await client.change_presence(game=discord.Game(name=video.filename, type=2))
            await video.add_to_db()
        except Exception:
            ei = sys.exc_info()
            try:
                await client.send_message(client.get_channel(config["Discord"]["main_channel"]),
                                          f"☢️ **ERRORE CRITICO NELL'AGGIORNAMENTO DELLA CODA DI VIDEO**\n"
                                          f"Il bot si è disconnesso dalla chat vocale, e ha svuotato la coda.\n"
                                          f"Una segnalazione di errore è stata automaticamente mandata a Steffo.\n\n"
                                          f"Dettagli dell'errore:\n"
                                          f"```python\n"
                                          f"{repr(ei[1])}\n"
                                          f"```")
                if voice_player is not None:
                    await voice_player.stop()
                voice_player = None
                await voice_client.disconnect()
                voice_client = None
                voice_queue = []
            except Exception as e:
                print("ERRORE CRITICO PIU' CRITICO:\n" + repr(e) + "\n\n" + repr(sys.exc_info()))
            sentry.captureException(exc_info=ei)


def process(users_connection=None):
    print("Discordbot starting...")
    if users_connection is not None:
        asyncio.ensure_future(update_users_pipe(users_connection))
    asyncio.ensure_future(update_music_queue())
    client.on_error = on_error
    client.run(config["Discord"]["bot_token"])


if __name__ == "__main__":
    process()
