import random
import re
# noinspection PyPackageRequirements
import discord
# noinspection PyPackageRequirements
import discord.opus
# noinspection PyPackageRequirements
import discord.voice_client
import functools
import sys
import db
import youtube_dl
import concurrent.futures
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
import sqlalchemy.exc

logging.getLogger().setLevel(level=logging.ERROR)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)

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
radio_messages = ["https://www.youtube.com/watch?v=3-yeK1Ck4yk",
                  "https://youtu.be/YcR7du_A1Vc",
                  "https://clyp.it/byg3i52l"]

song_special_messages = {
    "despacito": ":arrow_forward: this is so sad. alexa play {song}",
    "faded": ":arrow_forward: Basta Garf, lasciami ascoltare {song}",
    "ligma": ":arrow_forward: What is ligma? {song}!",
    "sugma": ":arrow_forward: What is sugma? {song}!",
    "sugondese": ":arrow_forward: What is sugondese? {song}!",
    "bofa": ":arrow_forward: What is bofa? {song}!",
    "updog": ":arrow_forward: What's up, dog? {song}!",
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

# Init the executor
executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

# Init the Sentry client
sentry = raven.Client(config["Sentry"]["token"],
                      release=version,
                      install_logger_hook=False,
                      hook_libraries=[])


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
    def __init__(self, url: str = None, file: str = None, info: dict = None, enqueuer: discord.Member = None):
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
        self.duration = None

    def __str__(self):
        if self.info is None or "title" not in self.info:
            return f"`{self.file}`"
        return f"_{self.info['title']}_"

    def plain_text(self):
        if self.info is None or "title" not in self.info:
            return self.file
        return self.info['title']

    async def download(self, progress_hooks: typing.List["function"] = None):
        # File already downloaded
        if self.downloaded:
            raise AlreadyDownloadedError()
        # No progress hooks
        if progress_hooks is None:
            progress_hooks = []
        # Check if under max duration
        self.duration = datetime.timedelta(seconds=self.info.get("duration", 0))
        if self.info is not None and self.duration.total_seconds() > int(config["YouTube"]["max_duration"]):
            raise DurationError()
        # Download the file
        logger.info(f"Now downloading {repr(self)}")
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

    def create_audio_source(self) -> discord.PCMVolumeTransformer:
        # Check if the file has been downloaded
        if not self.downloaded:
            raise FileNotDownloadedError()
        return discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f"./opusfiles/{self.file}", **ffmpeg_settings))


def command(func):
    """Decorator. Runs the function as a Discord command."""

    async def new_func(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str], *args,
                       **kwargs):
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
            result = await func(self, channel=channel, author=author, params=params, *args, **kwargs)
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


def requires_connected_voice_client(func):
    """Decorator. Ensures the voice client is connected before running the command."""

    async def new_func(self: "RoyalDiscordBot", channel: discord.TextChannel, author: discord.Member,
                       params: typing.List[str], *args, **kwargs):
        for voice_client in self.voice_clients:
            if voice_client.channel in self.main_guild.channels and voice_client.is_connected():
                break
        else:
            await channel.send("⚠️ Non sono connesso alla cv!\n"
                               "Fammi entrare scrivendo `!cv` mentre sei in chat vocale.")
            return
        return await func(self, channel=channel, author=author, params=params, *args, **kwargs)

    return new_func


def requires_rygdb(func, optional=False):
    async def new_func(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str], *args,
                       **kwargs):
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
        return await func(self, channel=channel, author=author, params=params, dbuser=dbuser, *args, **kwargs)

    return new_func


class RoyalDiscordBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_channel: typing.Optional[discord.TextChannel] = None
        self.main_guild: typing.Optional[discord.Guild] = None
        self.commands = {
            "!ping": self.cmd_ping,
            "!cv": self.cmd_cv,
            "!summon": self.cmd_cv,
            "!play": self.cmd_play,
            "!p": self.cmd_play,
            "!search": self.cmd_play,
            "!file": self.cmd_play,
            "!skip": self.cmd_skip,
            "!s": self.cmd_skip,
            "!remove": self.cmd_remove,
            "!cancel": self.cmd_remove,
            "!queue": self.cmd_queue,
            "!q": self.cmd_queue,
            "!shuffle": self.cmd_shuffle,
            "!clear": self.cmd_clear,
            "!register": self.cmd_register,
            "!forceplay": self.cmd_forceplay,
            "!fp": self.cmd_forceplay,
            "!radiomessages": self.cmd_radiomessages,
            "!yes": self.null,
            "!no": self.null,
            "!pause": self.cmd_pause,
            "!resume": self.cmd_resume
        }
        self.video_queue: typing.List[Video] = []
        self.now_playing = None
        self.radio_messages = False
        self.next_radio_message_in = int(config["Discord"]["radio_messages_every"])
        asyncio.ensure_future(self.queue_predownload_videos())
        asyncio.ensure_future(self.queue_play_next_video())

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
        if data[0] not in self.commands:
            await message.channel.send(":warning: Comando non riconosciuto.")
            return
        await self.commands[data[0]](channel=message.channel,
                                     author=message.author,
                                     params=data)

    async def on_error(self, event_method, *args, **kwargs):
        ei = sys.exc_info()
        logger.error(f"Critical error: {repr(ei[1])}")
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
            logger.error("Double critical error: {repr(sys.exc_info())}")
        loop.stop()
        sentry.captureException(exc_info=ei)
        exit(1)

    async def feed_pipe(self, connection):
        await self.wait_until_ready()
        while True:
            msg = await loop.run_in_executor(executor, connection.recv)
            logger.info(f"Received \"{msg}\" from the Telegram-Discord pipe.")
            if msg == "get cv":
                discord_members = list(self.main_guild.members)
                channels = {0: None}
                members_in_channels = {0: []}
                message = ""
                # Find all the channels
                for member in discord_members:
                    if member.voice is not None:
                        channel = members_in_channels.get(member.voice.channel.id)
                        if channel is None:
                            members_in_channels[member.voice.channel.id] = list()
                            channel = members_in_channels[member.voice.channel.id]
                            channels[member.voice.channel.id] = member.voice.channel
                        channel.append(member)
                    else:
                        members_in_channels[0].append(member)
                # Edit the message, sorted by channel
                for channel in channels:
                    members_in_channels[channel].sort(key=lambda x: x.nick if x.nick is not None else x.name)
                    if channel == 0:
                        message += "Non in chat vocale:\n"
                    else:
                        message += f"In #{channels[channel].name}:\n"
                    for member in members_in_channels[channel]:
                        if member.status == discord.Status.offline and member.voice.channel is None:
                            continue
                        # Online status emoji
                        if member.bot:
                            message += "🤖 "
                        elif member.status == discord.Status.online:
                            message += "🔵 "
                        elif member.status == discord.Status.idle:
                            message += "⚫️ "
                        elif member.status == discord.Status.dnd:
                            message += "🔴 "
                        elif member.status == discord.Status.offline:
                            message += "⚪️ "
                        # Voice
                        if channel != 0:
                            # Voice status
                            if member.voice.self_deaf:
                                message += f"🔇 "
                            elif member.voice.self_mute:
                                message += f"🔈 "
                            else:
                                message += f"🔊 "
                        # Nickname
                        if member.nick is not None:
                            message += member.nick
                        else:
                            message += member.name
                        # Game or stream
                        if member.activity is not None:
                            if member.activity == discord.ActivityType.playing:
                                message += f" | 🎮 {member.activity.name}"
                            elif member.activity == discord.ActivityType.streaming:
                                message += f" | 📡 [{member.activity.name}]({member.activity.url})"
                            elif member.activity == discord.ActivityType.listening:
                                message += f" | 🎧 {member.activity.name}"
                            elif member.activity.type == discord.ActivityType.watching:
                                message += f" | 📺 {member.activity.name}"
                        message += "\n"
                    message += "\n"
                connection.send(message)
            elif msg.startswith("!"):
                data = msg.split(" ")
                if data[0] not in self.commands:
                    connection.send("error")
                    continue
                await self.main_channel.send(f"{msg}\n"
                                             f"_(da Telegram)_")
                await self.commands[data[0]](channel=self.get_channel(config["Discord"]["main_channel"]),
                                             author=None,
                                             params=data)
                connection.send("success")

    async def queue_predownload_videos(self):
        while True:
            for index, video in enumerate(self.video_queue[:int(config["YouTube"]["predownload_videos"])].copy()):
                if video.downloaded:
                    continue
                try:
                    with async_timeout.timeout(int(config["YouTube"]["download_timeout"])):
                        await video.download()
                except asyncio.TimeoutError:
                    await self.main_channel.send(f"⚠️ Il download di {str(video)} ha richiesto più di"
                                                 f" {config['YouTube']['download_timeout']} secondi, pertanto è stato"
                                                 f" rimosso dalla coda.")
                    del self.video_queue[index]
                    continue
                except DurationError:
                    await self.main_channel.send(f"⚠️ {str(video)} dura più di"
                                                 f" {str(int(config['YouTube']['max_duration']) // 60)}"
                                                 f" minuti, quindi è stato rimosso dalla coda.")
                    del self.video_queue[index]
                    continue
                except Exception as e:
                    await self.main_channel.send(f"⚠️ E' stato incontrato un errore durante il download di "
                                                 f"{str(video)}, quindi è stato rimosso dalla coda.\n\n"
                                                 f"**Dettagli sull'errore:**\n"
                                                 f"```python\n"
                                                 f"{str(e)}"
                                                 f"```")
                    del self.video_queue[index]
                    continue
            await asyncio.sleep(1)

    async def queue_play_next_video(self):
        await self.wait_until_ready()
        while True:
            # Fun things will happen with multiple voice clients!
            for voice_client in self.voice_clients:
                if not voice_client.is_connected() \
                        or voice_client.is_playing():
                    continue
                if len(self.video_queue) == 0:
                    self.now_playing = None
                    await self.change_presence()
                    continue
                now_playing = self.video_queue[0]
                try:
                    audio_source = now_playing.create_audio_source()
                except FileNotDownloadedError:
                    continue
                logger.info(f"Started playing {repr(now_playing)}")
                voice_client.play(audio_source)
                del self.video_queue[0]
                activity = discord.Activity(name=now_playing.plain_text(),
                                            type=discord.ActivityType.playing)
                await self.change_presence(status=discord.Status.online, activity=activity)
                if now_playing.enqueuer is not None:
                    try:
                        session = db.Session()
                        enqueuer = await loop.run_in_executor(executor, session.query(db.Discord)
                                                              .filter_by(discord_id=now_playing.enqueuer.id)
                                                              .one_or_none)
                        played_music = db.PlayedMusic(enqueuer=enqueuer,
                                                      filename=now_playing.plain_text(),
                                                      timestamp=datetime.datetime.now())
                        session.add(played_music)
                        await loop.run_in_executor(executor, session.commit)
                        await loop.run_in_executor(executor, session.close)
                    except sqlalchemy.exc.OperationalError:
                        pass
                for key in song_special_messages:
                    if key in now_playing.file.lower():
                        await self.main_channel.send(song_special_messages[key].format(song=str(now_playing)))
                        break
                else:
                    await self.main_channel.send(f":arrow_forward: Ora in riproduzione: {str(now_playing)}")
            await asyncio.sleep(1)

    async def add_video_from_url(self, url, index: typing.Optional[int] = None, enqueuer: discord.Member = None):
        # Retrieve info
        with youtube_dl.YoutubeDL({"quiet": True,
                                   "ignoreerrors": True,
                                   "simulate": True}) as ytdl:
            info = await loop.run_in_executor(executor,
                                              functools.partial(ytdl.extract_info, url=url, download=False))
        if info is None:
            await self.main_channel.send(f"⚠ Non è stato trovato nessun video all'URL `{url}`,"
                                         f" pertanto non è stato aggiunto alla coda.")
            return
        if "entries" in info:
            # This is a playlist
            for entry in info["entries"]:
                if index is not None:
                    self.video_queue.insert(index, Video(url=entry["webpage_url"], info=entry, enqueuer=enqueuer))
                else:
                    self.video_queue.append(Video(url=entry["webpage_url"], info=entry, enqueuer=enqueuer))
            return
        # This is a single video
        if index is not None:
            self.video_queue.insert(index, Video(url=url, info=info, enqueuer=enqueuer))
        else:
            self.video_queue.append(Video(url=url, info=info, enqueuer=enqueuer))

    async def add_video_from_file(self, file, index: typing.Optional[int] = None, enqueuer: discord.Member = None):
        if index is not None:
            self.video_queue.insert(index, Video(file=file, enqueuer=enqueuer))
        else:
            self.video_queue.append(Video(file=file, enqueuer=enqueuer))

    @command
    async def null(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        pass

    @command
    async def cmd_ping(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        await channel.send(f"Pong!")

    @command
    async def cmd_register(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
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

    @command
    async def cmd_cv(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        """Summon the bot in the author's voice channel."""
        if author is None:
            await channel.send("⚠ Questo comando richiede un autore.")
            return
        if author.voice is None:
            await channel.send("⚠ Non sei in nessun canale!")
            return
        if author.voice.channel == self.main_guild.afk_channel:
            await channel.send("⚠ Non posso connettermi al canale AFK!")
            return
        if author.voice.channel.bitrate < 64000:
            await channel.send("ℹ️ Sei in un canale con un bitrate ridotto.\n"
                               "L'utilizzo del bot in quel canale ignorerà il limite di bitrate e potrebbe causare lag"
                               " o eccessivo consumo di dati.\n"
                               "Se vuoi procedere comunque, scrivi `!yes`.")
            try:
                await self.wait_for("message", check=lambda m: m.content == "!yes", timeout=10.0)
            except asyncio.TimeoutError:
                return
        # Check if there's already a connected client
        for voice_client in self.voice_clients:
            if voice_client.channel in self.main_guild.channels and voice_client.is_connected():
                await voice_client.move_to(author.voice.channel)
                await channel.send(f"⤵️ Mi sono spostato in <#{author.voice.channel.id}>.")
                break
        else:
            await author.voice.channel.connect()
            await channel.send(f"⤵️ Mi sono connesso in <#{author.voice.channel.id}>.")

    @command
    @requires_connected_voice_client
    async def cmd_play(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        if len(params) < 2:
            await channel.send("⚠ Non hai specificato una canzone da riprodurre!\n"
                               "Sintassi: `!play <url|ricercayoutube|nomefile>`")
            return
        channel.typing()
        # If the radio messages are enabled...
        if self.radio_messages:
            self.next_radio_message_in -= 1
            if self.next_radio_message_in <= 0:
                radio_message = random.sample(radio_messages, 1)[0]
                self.next_radio_message_in = int(config["Discord"]["radio_messages_every"])
                await self.add_video_from_url(radio_message)
                await channel.send(f"📻 Aggiunto un messaggio radio, disattiva con `!radiomessages off`.")
        # Parse the parameter as URL
        url = re.match(r"(?:https?://|ytsearch[0-9]*:).*", " ".join(params[1:]).strip("<>"))
        if url is not None:
            # This is a url
            await self.add_video_from_url(url.group(0), enqueuer=author)
            await channel.send(f"✅ Video aggiunto alla coda.")
            return
        # Parse the parameter as file
        file_path = os.path.join(os.path.join(os.path.curdir, "opusfiles"), " ".join(params[1:]))
        if os.path.exists(file_path):
            # This is a file
            await self.add_video_from_file(file=file_path, enqueuer=author)
            await channel.send(f"✅ Video aggiunto alla coda.")
            return
        file_path += ".opus"
        if os.path.exists(file_path):
            # This is a file
            await self.add_video_from_file(file=file_path, enqueuer=author)
            await channel.send(f"✅ Video aggiunto alla coda.")
            return
        # Search the parameter on youtube
        search = " ".join(params[1:])
        # This is a search
        await self.add_video_from_url(url=f"ytsearch:{search}", enqueuer=author)
        await channel.send(f"✅ Video aggiunto alla coda.")

    @command
    @requires_connected_voice_client
    async def cmd_skip(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        for voice_client in self.voice_clients:
            if voice_client.is_playing():
                voice_client.stop()
                await channel.send(f"⏩ Video saltato.")
                break
        else:
            await channel.send("⚠ Non c'è nessun video in riproduzione.")

    @command
    @requires_connected_voice_client
    async def cmd_remove(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        if len(self.video_queue) == 0:
            await channel.send("⚠ Non c'è nessun video in coda.")
            return
        if len(params) == 1:
            index = len(self.video_queue) - 1
        else:
            try:
                index = int(params[1]) - 1
            except ValueError:
                await channel.send("⚠ Il numero inserito non è valido.\n"
                                   "Sintassi: `!remove [numerovideoiniziale] [numerovideofinale]`")
                return
        if len(params) < 3:
            if abs(index) >= len(self.video_queue):
                await channel.send("⚠ Il numero inserito non corrisponde a nessun video nella playlist.\n"
                                   "Sintassi: `!remove [numerovideoiniziale] [numerovideofinale]`")
                return
            video = self.video_queue.pop(index)
            await channel.send(f":regional_indicator_x: {str(video)} è stato rimosso dalla coda.")
            return
        try:
            start = int(params[1]) - 1
        except ValueError:
            await channel.send("⚠ Il numero iniziale inserito non è valido.\n"
                               "Sintassi: `!remove [numerovideoiniziale] [numerovideofinale]`")
            return
        if start >= len(self.video_queue):
            await channel.send("⚠ Il numero iniziale inserito non corrisponde a nessun video nella"
                               " playlist.\n"
                               "Sintassi: `!remove [numerovideoiniziale] [numerovideofinale]`")
            return
        try:
            end = int(params[2]) - 2
        except ValueError:
            await channel.send("⚠ Il numero finale inserito non è valido.\n"
                               "Sintassi: `!remove [numerovideoiniziale] [numerovideofinale]`")
            return
        if end >= len(self.video_queue):
            await channel.send("⚠ Il numero finale inserito non corrisponde a nessun video nella"
                               " playlist.\n"
                               "Sintassi: `!remove [numerovideoiniziale] [numerovideofinale]`")
            return
        if start > end:
            await channel.send("⚠ Il numero iniziale è maggiore del numero finale.\n"
                               "Sintassi: `!remove [numerovideoiniziale] [numerovideofinale]`")
            return
        del self.video_queue[start:end]
        await channel.send(f":regional_indicator_x: {end - start} video rimossi dalla coda.")

    @command
    async def cmd_queue(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        if len(self.video_queue) == 0:
            await channel.send("**Video in coda:**\n"
                               "nessuno")
            return
        msg = "**Video in coda:**\n"
        for index, video in enumerate(self.video_queue[:10]):
            msg += f"{queue_emojis[index]} {str(video)}\n"
        if len(self.video_queue) > 10:
            msg += f"più altri {len(self.video_queue) - 10} video!"
        await channel.send(msg)

    @command
    @requires_connected_voice_client
    async def cmd_shuffle(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        if len(self.video_queue) == 0:
            await channel.send("⚠ Non ci sono video in coda!")
            return
        random.shuffle(self.video_queue)
        await channel.send("♠️ ♦️ ♣️ ♥️ Shuffle completo!")

    @command
    @requires_connected_voice_client
    async def cmd_clear(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        if len(self.video_queue) == 0:
            await channel.send("⚠ Non ci sono video in coda!")
            return
        self.video_queue = []
        await channel.send(":regional_indicator_x: Tutti i video in coda rimossi.")

    @command
    @requires_connected_voice_client
    async def cmd_forceplay(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        if len(params) < 2:
            await channel.send("⚠ Non hai specificato una canzone da riprodurre!\n"
                               "Sintassi: `!forceplay <url|ricercayoutube|nomefile>`")
            return
        for voice_client in self.voice_clients:
            if voice_client.is_playing():
                voice_client.stop()
        # Parse the parameter as URL
        url = re.match(r"(?:https?://|ytsearch[0-9]*:).*", " ".join(params[1:]).strip("<>"))
        if url is not None:
            # This is a url
            await self.add_video_from_url(url.group(0), enqueuer=author, index=0)
            await channel.send(f"✅ Riproduzione del video forzata.")
            return
        # Parse the parameter as file
        file_path = os.path.join(os.path.join(os.path.curdir, "opusfiles"), " ".join(params[1:]))
        if os.path.exists(file_path):
            # This is a file
            await self.add_video_from_file(file=file_path, enqueuer=author, index=0)
            await channel.send(f"✅ Riproduzione del video forzata.")
            return
        file_path += ".opus"
        if os.path.exists(file_path):
            # This is a file
            await self.add_video_from_file(file=file_path, enqueuer=author, index=0)
            await channel.send(f"✅ Riproduzione del video forzata.")
            return
        # Search the parameter on youtube
        search = " ".join(params[1:])
        # This is a search
        await self.add_video_from_url(url=f"ytsearch:{search}", enqueuer=author, index=0)
        await channel.send(f"✅ Riproduzione del video forzata.")

    @command
    async def cmd_radiomessages(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        if len(params) < 2:
            self.radio_messages = not self.radio_messages
        else:
            if params[1].lower() == "on":
                self.radio_messages = True
            elif params[1].lower() == "off":
                self.radio_messages = False
            else:
                await channel.send("⚠ Sintassi del comando non valida.\n"
                                   "Sintassi: `!radiomessages [on|off]`")
                return
        await channel.send(f"📻 Messaggi radio **{'attivati' if self.radio_messages else 'disattivati'}**.")

    @command
    @requires_connected_voice_client
    async def cmd_pause(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        for voice_client in self.voice_clients:
            if voice_client.is_playing():
                voice_client.pause()
                await channel.send(f"⏸ Riproduzione messa in pausa.\n"
                                   f"Riprendi con `!resume`.")

    @command
    @requires_connected_voice_client
    async def cmd_resume(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        for voice_client in self.voice_clients:
            if voice_client.is_playing():
                voice_client.resume()
                await channel.send(f"⏯ Riproduzione ripresa.")


def process(users_connection=None):
    logger.info("Initializing the bot...")
    bot = RoyalDiscordBot()
    if users_connection is not None:
        logger.info("Initializing Telegram-Discord connection...")
        asyncio.ensure_future(bot.feed_pipe(users_connection))
    logger.info("Logging in...")
    loop.run_until_complete(bot.login(config["Discord"]["bot_token"], bot=True))
    logger.info("Connecting...")
    try:
        loop.run_until_complete(bot.connect())
    except KeyboardInterrupt:
        logger.info("Now stopping...")
        loop.run_until_complete(bot.logout())
        exit(0)


if __name__ == "__main__":
    process()
