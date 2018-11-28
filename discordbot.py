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
import typing
import os
import asyncio
import configparser
import async_timeout
import raven
import logging
import errors
import datetime
import sqlalchemy.exc
import coloredlogs
import errors
import math

logging.getLogger().disabled = True
logger = logging.getLogger(__name__)
os.environ["COLOREDLOGS_LOG_FORMAT"] = "%(asctime)s %(levelname)s %(name)s %(message)s"
coloredlogs.install(level="DEBUG", logger=logger)

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

# Zalgo text
zalgo_up = ['̍', '̎', '̄', '̅', '̿', '̑', '̆', '̐', '͒', '͗', '͑', '̇', '̈', '̊', '͂', '̓', '̈́', '͊',
            '͋', '͌', '̃', '̂', '̌', '͐', '́', '̋', '̏', '̽', '̉', 'ͣ', 'ͤ', 'ͥ', 'ͦ', 'ͧ', 'ͨ', 'ͩ',
            'ͪ', 'ͫ', 'ͬ', 'ͭ', 'ͮ', 'ͯ', '̾', '͛', '͆', '̚', ]
zalgo_down = ['̖', '̗', '̘', '̙', '̜', '̝', '̞', '̟', '̠', '̤', '̥', '̦', '̩', '̪', '̫', '̬', '̭', '̮',
              '̯', '̰', '̱', '̲', '̳', '̹', '̺', '̻', '̼', 'ͅ', '͇', '͈', '͉', '͍', '͎', '͓', '͔', '͕',
              '͖', '͙', '͚', '', ]
zalgo_middle = ['̕', '̛', '̀', '́', '͘', '̡', '̢', '̧', '̨', '̴', '̵', '̶', '͜', '͝', '͞', '͟', '͠', '͢',
                '̸', '̷', '͡', ]

# Init the event loop
loop = asyncio.get_event_loop()

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
    "country road": ":arrow_forward: Take me home, to {song}, the place I belong!",
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
    "magicite": "⚠️ Warning: {song} contiene numerosi bug. E' ora in riproduzione.",
    "papers please": ":arrow_forward: Glory to Arstotzka! {song}!",
    "we are number one": ":arrow_forward: Now paying respect to Robbie Rotten: {song}",
    "jump up superstar": ":arrow_forward: Is {song} the Tengen Toppa Guren Lagann opening?",
    "the world revolving": ":arrow_forward: CHAOS! CHAOS! I CAN DO {song}!",
    "deltarune": ":arrow_forward: You hug Ralsei. A strange music starts playing: {song}",
    "song of unhealing": ":arrow_forward: BEN {song}",
    "police academy": ":arrow_forward: {song} - freedom.png",
    "super smash bros. ultimate": ":arrow_forward: Re-awaken the undying light with {song}!",
    "powerwolf": ":arrow_forward: Spaggia, ma non ti sei un po' stancato di {song}?",
    "eurobeat": ":arrow_forward: Nemesis approva la scelta di {song}. Ben fatto, amico."   
}

# FFmpeg settings
ffmpeg_settings = {}

# Init the executor
executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)


class Succ:
    """All calls to this class return itself."""

    def __bool__(self):
        return False
    
    def __getattr__(self):
        return Succ()

    def __call__(self, *args, **kwargs):
        return Succ()

    def __str__(self):
        return "succ"

    def __repr__(self):
        return "<Succ>"


# Init the Sentry client
if config.get("Sentry") and config["Sentry"].get("token"):
    sentry = raven.Client(config["Sentry"]["token"],
                        release=raven.fetch_git_sha(os.path.dirname(__file__)),
                        install_logging_hook=False,
                        hook_libraries=[])
else:
    logger.warning("Sentry not set, ignoring all calls to it.")
    sentry = Succ()


class Video:
    """A video to be played in the bot."""

    def __init__(self, url: str = None, file: str = None, info: dict = None, enqueuer: discord.Member = None):
        # Url of the video if it has to be downloaded
        self.url = url
        # Filename of the downloaded video
        if file is None and info is None:
            # Get it from the url hash
            self.file = str(hash(url)) + ".opus"
        elif info is not None:
            # Get it from the video title
            self.file = "./opusfiles/" + re.sub(r'[/\\?*"<>|!:]', "_", info["title"]) + ".opus"
        else:
            # The filename was explicitly passed
            self.file = file
        # Was the file already downloaded?
        self.downloaded = (file is not None)
        # Do we already have info on the video?
        self.info = info
        # Who added the video to the queue?
        self.enqueuer = enqueuer
        # How long and what title has the video?
        if info is not None:
            self.duration = info.get("duration")
            self.title = info.get("title")
        else:
            self.duration = None
            self.title = None
        # No audio source exists yet
        self.audio_source = None

    def __str__(self):
        """Format the title to be used on Discord using Markdown."""
        if self.info is None or "title" not in self.info:
            return f"`{self.file}`"
        return f"_{self.info['title']}_"

    def __repr__(self):
        return f"<discordbot.Video {str(self)}>"

    def plain_text(self):
        """Format the video title without any Markdown."""
        if self.info is None or "title" not in self.info:
            return self.file
        return self.info['title']

    def download(self, progress_hooks: typing.List["function"] = None):
        # File already downloaded
        if self.downloaded:
            raise errors.AlreadyDownloadedError()
        # No progress hooks
        if progress_hooks is None:
            progress_hooks = []
        # Check if under max duration
        self.duration = datetime.timedelta(seconds=self.info.get("duration", 0))
        # Refuse downloading if over YouTube max_duration
        if self.info is not None and self.duration.total_seconds() > self.max_duration:
            raise errors.DurationError()
        # Download the file
        logger.info(f"Downloading: {repr(self)}")
        with youtube_dl.YoutubeDL({"noplaylist": True,
                                   "format": "best",
                                   "postprocessors": [{
                                       "key": 'FFmpegExtractAudio',
                                       "preferredcodec": 'opus'
                                   }],
                                   "outtmpl": self.file,
                                   "progress_hooks": progress_hooks,
                                   "quiet": True}) as ytdl:
            ytdl.download(self.url)
        logger.info(f"Download complete: {repr(self)}")
        self.downloaded = True

    def load(self) -> None:
        # Check if the file has been downloaded
        if not self.downloaded:
            raise errors.FileNotDownloadedError()
        self.audio_source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f"{self.file}", **ffmpeg_settings))


class VideoQueue():
    """The queue of videos to be played."""

    def __init__(self):
        self.list: typing.List[Video] = []
        self.now_playing: typing.Optional[Video] = None

    def __len__(self) -> int:
        return len(self.list)

    def add(self, video: Video, position: int=None) -> None:
        if position is None:
            self.list.append(video)
            return
        self.list.insert(position, video)
    
    def next_video(self) -> typing.Optional[Video]:
        if len(self.list) == 0:
            return None
        return self.list[0]

    def shuffle(self):
        random.shuffle(self.list)

    def clear(self):
        self.list = None
        self.now_playing = None

    def forward(self) -> None:
        self.now_playing = self.list.pop(0)

    def find_video(self, title: str) -> typing.Optional[Video]:
        """Returns the first video with a certain title (or filename)."""
        for video in self.list:
            if title in video.title:
                return video
            elif title in video.file:
                return video
        return None
    
    def __getitem__(self, index: int) -> Video:
        """Get an element from the list."""
        return self.list[index]


class SecretVideo(Video):
    """A video to be played, but with a Zalgo'ed title."""

    def __str__(self):
        final_string = ""
        for letter in self.file:
            final_string += random.sample(zalgo_up, 1)[0]
            final_string += random.sample(zalgo_middle, 1)[0]
            final_string += random.sample(zalgo_down, 1)[0]
            final_string += letter
        return final_string

    def plain_text(self):
        final_string = ""
        for letter in self.file:
            final_string += random.sample(zalgo_up, 1)[0]
            final_string += random.sample(zalgo_middle, 1)[0]
            final_string += random.sample(zalgo_down, 1)[0]
            final_string += letter
        return final_string


def escape(message: str):
    return message.replace("<", "&lt;").replace(">", "&gt;")


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
            # noinspection PyBroadException
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
            "!next": self.cmd_skip,
            "!remove": self.cmd_remove,
            "!r": self.cmd_remove,
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
        self.video_queue: VideoQueue = VideoQueue()
        self.load_config("config.ini")
        self.inactivity_timer = 0

    def load_config(self, filename):
    # Init the config reader
    config = configparser.ConfigParser()
    config.read("config.ini")
    # Token
    try:
        self.token = config["Discord"]["bot_token"]
    except KeyError, ValueError:
        raise errors.InvalidConfigError("Missing Discord bot token.")
    # Main channels, will be fully loaded when ready
    try:
        self.main_guild_id = int(config["Discord"]["server_id"])
        self.main_channel_id = int(config["Discord"]["main_channel"]
    except KeyError, ValueError:
        raise errors.InvalidConfigError("Missing main guild and channel ids.")
    # Max enqueable video duration
    try:
        self.max_duration = int(config["YouTube"].get("max_duration"))
    except KeyError, ValueError:
        logger.warning("Max video duration is not set, setting it to infinity.")
        self.max_duration = math.inf
    # Max videos to predownload
    try:
        self.max_videos_to_predownload = int(config["YouTube"]["predownload_videos"])
    except KeyError, ValueError:
        logger.warning("Max videos to predownload is not set, setting it to infinity.")
        self.max_videos_to_predownload = None
    # Radio messages
    try:
        self.radio_messages_enabled = True if config["Discord"]["radio_messages_enabled"] == "True" else False
        self.radio_messages_every = int(config["Discord"]["radio_messages_every"])
        self.radio_messages_next_in = self.radio_messages_every
    except KeyError, ValueError:
        logger.warning("Radio messages config error, disabling them.")
        self.radio_messages_enabled = False
        self.radio_messages_every = mathf.inf
        self.radio_messages_next_in = mathf.inf

    async def on_ready(self):
        # Get the main guild
        self.main_guild = self.get_guild(self.main_guild_id)
        if not isinstance(self.main_guild, discord.Guild):
            raise errors.InvalidConfigError("The main guild does not exist!")
        # Get the main channel
        self.main_channel = self.get_channel(self.main_channel_id)
        if not isinstance(self.main_channel, discord.TextChannel):
            raise errors.InvalidConfigError("The main channel is not a TextChannel!")
        # Show yourself!
        await self.change_presence(status=discord.Status.online, activity=None)
        logger.info("Bot is ready!")
        # Start the bot tasks
        asyncio.ensure_future(self.queue_predownload_videos())
        asyncio.ensure_future(self.queue_play_next_video())
        asyncio.ensure_future(self.inactivity_countdown())
        asyncio.ensure_future(self.activity_task())

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
        logger.debug(f"Received command: {message.content}")
        sentry.extra_context({
            "command": data[0],
            "message": message
        })
        self.inactivity_timer = 3600
        await self.commands[data[0]](channel=message.channel,
                                     author=message.author,
                                     params=data)

    async def on_error(self, event_method, *args, **kwargs):
        ei = sys.exc_info()
        logger.error(f"Critical error: {repr(ei[1])}")
        # noinspection PyBroadException
        try:
            await self.main_channel.send(f"☢️ **ERRORE CRITICO NELL'EVENTO** `{event_method}`!\n"
                                         f"Il bot si è chiuso e si dovrebbe riavviare entro qualche minuto.\n"
                                         f"Una segnalazione di errore è stata automaticamente mandata a Steffo.\n\n"
                                         f"Dettagli dell'errore:\n"
                                         f"```python\n"
                                         f"{repr(ei[1])}\n"
                                         f"```")
            await self.change_presence(status=discord.Status.invisible)
            await self.close()
        except Exception:
            logger.error(f"Double critical error: {sys.exc_info()}")
        loop.stop()
        sentry.captureException(exc_info=ei)
        exit(1)

    async def feed_pipe(self, connection):
        await self.wait_until_ready()
        while True:
            msg = await loop.run_in_executor(executor, connection.recv)
            logger.debug(f"Received from the Telegram-Discord pipe: {msg}")
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
                for channel in sorted(channels, key=lambda c: -c):
                    members_in_channels[channel].sort(key=lambda x: x.nick if x.nick is not None else x.name)
                    if channel == 0:
                        message += "<b>Non in chat vocale:</b>\n"
                    else:
                        message += f"<b>In #{escape(channels[channel].name)}:</b>\n"
                    for member in members_in_channels[channel]:
                        # Ignore not-connected non-notable members
                        if channel == 0 and len(member.roles) < 2:
                            continue
                        # Ignore offline members
                        if member.status == discord.Status.offline and member.voice is None:
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
                            message += escape(member.nick)
                        else:
                            message += escape(member.name)
                        # Game or stream
                        if member.activity is not None:
                            if member.activity.type == discord.ActivityType.playing:
                                message += f" | 🎮 {escape(member.activity.name)}"
                                # Rich presence
                                try:
                                    if member.activity.state is not None:
                                        message += f" ({escape(member.activity.state)})"
                                except AttributeError:
                                    try:
                                        if member.activity.details is not None:
                                            message += f" ({escape(member.activity.details)})"
                                    except AttributeError:
                                        pass
                            elif member.activity.type == discord.ActivityType.streaming:
                                message += f" | 📡 [{escape(member.activity.name)}]({escape(member.activity.url)})"
                            elif member.activity.type == discord.ActivityType.listening:
                                message += f" | 🎧 {escape(member.activity.name)}"
                            elif member.activity.type == discord.ActivityType.watching:
                                message += f" | 📺 {escape(member.activity.name)}"
                        message += "\n"
                    message += "\n"
                connection.send(message)
                logger.debug(f"Answered successfully cvlist request.")
            elif msg.startswith("!"):
                data = msg.split(" ")
                if data[0] not in self.commands:
                    connection.send("error")
                    continue
                logger.debug(f"Received command: {msg}")
                await self.main_channel.send(f"{msg}\n"
                                             f"_(da Telegram)_")
                await self.commands[data[0]](channel=self.main_channel,
                                             author=None,
                                             params=data)
                connection.send("success")

    async def queue_predownload_videos(self):
        while True:
            for index, video in enumerate(self.video_queue.list[:(None if self.max_videos_to_predownload == math.inf else self.max_videos_to_predownload].copy()):
                if video.downloaded:
                    continue
                try:
                    with async_timeout.timeout(int(config["YouTube"]["download_timeout"])):
                        await loop.run_in_executor(executor, video.download)
                except asyncio.TimeoutError:
                    logger.warning(f"Video download took more than {config['YouTube']['download_timeout']}s:"
                                   f" {video.plain_text()}")
                    await self.main_channel.send(f"⚠️ Il download di {str(video)} ha richiesto più di"
                                                 f" {config['YouTube']['download_timeout']} secondi, pertanto è stato"
                                                 f" rimosso dalla coda.")
                    del self.video_queue.list[index]
                    continue
                except DurationError:
                    await self.main_channel.send(f"⚠️ {str(video)} dura più di"
                                                 f" {self.max_duration // 60}"
                                                 f" minuti, quindi è stato rimosso dalla coda.")
                    del self.video_queue.list[index]
                    continue
                except Exception as e:
                    sentry.user_context({
                        "discord": {
                            "discord_id": video.enqueuer.id,
                            "name": video.enqueuer.name,
                            "discriminator": video.enqueuer.discriminator
                        }
                    })
                    sentry.extra_context({
                        "video": video.plain_text()
                    })
                    sentry.captureException()
                    logger.error(f"Video download error: {str(e)}")
                    await self.main_channel.send(f"⚠️ E' stato incontrato un errore durante il download di "
                                                 f"{str(video)}, quindi è stato rimosso dalla coda.\n\n"
                                                 f"**Dettagli sull'errore:**\n"
                                                 f"```python\n"
                                                 f"{str(e)}"
                                                 f"```")
                    del self.video_queue.list[index]
                    continue
            await asyncio.sleep(1)

    async def queue_play_next_video(self):
        await self.wait_until_ready()
        while True:
            # TODO
            raise NotImplementedError("queue_play_next_video isn't done yet!")

    async def inactivity_countdown(self):
        while True:
            await asyncio.sleep(1)
            if self.inactivity_timer > 0:
                self.inactivity_timer -= 1
                continue
            for voice_client in self.voice_clients:
                if voice_client.is_connected():
                    logger.info("Disconnecting due to inactivity.")
                    await voice_client.disconnect()
                    await self.change_presence(status=discord.Status.online, activity=None)
                    await self.main_channel.send("💤 Mi sono disconnesso dalla cv per inattività.")

    async def create_activityreport(self):
        logger.debug("Fetching Discord users...")
        discord_users = list(self.main_guild.members)
        online_members_count = 0
        ingame_members_count = 0
        cv_count = 0
        cv_members_count = 0
        non_empty_channels = []
        for member in discord_users:
            if member.bot:
                continue
            if member.voice is not None and member.voice.channel != self.main_guild.afk_channel:
                cv_count += 1
                if member.voice.channel.id not in non_empty_channels:
                    non_empty_channels.append(member.voice.channel.id)
            if len(member.roles) >= 2:
                if member.voice is not None and member.voice.channel != self.main_guild.afk_channel:
                    cv_members_count += 1
                if member.status != discord.Status.offline and member.status != discord.Status.idle:
                    online_members_count += 1
                if member.activity is not None and member.activity.type == discord.ActivityType.playing:
                    ingame_members_count += 1
        logger.debug("Creating and committing db.ActivityReport...")
        session = db.Session()
        activityreport = db.ActivityReport(timestamp=datetime.datetime.now(),
                                           discord_members_online=online_members_count,
                                           discord_members_ingame=ingame_members_count,
                                           discord_cv=cv_count,
                                           discord_members_cv=cv_members_count,
                                           discord_channels_used=len(non_empty_channels))
        session.add(activityreport)
        await loop.run_in_executor(executor, session.commit)
        await loop.run_in_executor(executor, session.close)
        logger.info("ActivityReport created.")

    async def activity_task(self):
        await self.wait_until_ready()
        time_to_wait = int(config["Discord"]["activityreport_sample_time"])
        while True:
            await self.create_activityreport()
            logger.debug(f"Waiting {time_to_wait} seconds before the next record.")
            await asyncio.sleep(time_to_wait)

    async def add_video_from_url(self, url, index: typing.Optional[int] = None, enqueuer: discord.Member = None):
        # Retrieve info
        logger.debug(f"Retrieving info for {url}.")
        with youtube_dl.YoutubeDL({"quiet": True,
                                   "ignoreerrors": True,
                                   "simulate": True}) as ytdl:
            info = await loop.run_in_executor(executor,
                                              functools.partial(ytdl.extract_info, url=url, download=False))
        if info is None:
            logger.debug(f"No video found at {url}.")
            await self.main_channel.send(f"⚠ Non è stato trovato nessun video all'URL `{url}`,"
                                         f" pertanto non è stato aggiunto alla coda.")
            return
        if "entries" in info:
            logger.debug(f"Playlist detected at {url}.")
            for entry in info["entries"]:
                self.video_queue.add(Video(url=entry["webpage_url"], info=entry, enqueuer=enqueuer), index)
            return
        logger.debug(f"Single video detected at {url}.")
        self.video_queue.add(Video(url=entry["webpage_url"], info=entry, enqueuer=enqueuer), index)

    async def add_video_from_file(self, file, index: typing.Optional[int] = None, enqueuer: discord.Member = None):
        self.video_queue.add(Video(file=file, enqueuer=enqueuer), index)

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
                logger.info(f"Moving to {author.voice.channel.name}.")
                await voice_client.move_to(author.voice.channel)
                await channel.send(f"⤵️ Mi sono spostato in <#{author.voice.channel.id}>.")
                break
        else:
            logger.info(f"Connecting to {author.voice.channel.name}.")
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
        self.next_radio_message_in -= 1
        if self.next_radio_message_in <= 0:
            radio_message = random.sample(radio_messages, 1)[0]
            self.next_radio_message_in = self.radio_messages_every
            await self.add_video_from_url(radio_message)
            await channel.send(f"📻 Aggiunto un messaggio radio, disattiva con `!radiomessages off`.")
            logger.info(f"Radio message added to the queue.")
        # Parse the parameter as URL
        url = re.match(r"(?:https?://|ytsearch[0-9]*:).*", " ".join(params[1:]).strip("<>"))
        if url is not None:
            # This is a url
            await self.add_video_from_url(url.group(0), enqueuer=author)
            await channel.send(f"✅ Video aggiunto alla coda.")
            logger.debug(f"Added {url} to the queue as URL.")
            return
        # Parse the parameter as file
        file_path = os.path.join(os.path.join(os.path.curdir, "opusfiles"), " ".join(params[1:]))
        if os.path.exists(file_path):
            # This is a file
            await self.add_video_from_file(file=file_path, enqueuer=author)
            await channel.send(f"✅ Video aggiunto alla coda.")
            logger.debug(f"Added {file_path} to the queue as file.")
            return
        file_path += ".opus"
        if os.path.exists(file_path):
            # This is a file
            await self.add_video_from_file(file=file_path, enqueuer=author)
            await channel.send(f"✅ Video aggiunto alla coda.")
            logger.debug(f"Added {file_path} to the queue as file.")
            return
        # Search the parameter on youtube
        search = " ".join(params[1:])
        # This is a search
        await self.add_video_from_url(url=f"ytsearch:{search}", enqueuer=author)
        await channel.send(f"✅ Video aggiunto alla coda.")
        logger.debug(f"Added ytsearch:{search} to the queue as YouTube search.")

    @command
    @requires_connected_voice_client
    async def cmd_skip(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        for voice_client in self.voice_clients:
            if voice_client.is_playing():
                voice_client.stop()
                await channel.send(f"⏩ Video saltato.")
                logger.debug(f"A song was skipped.")
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
            video = self.video_queue.list.pop(index)
            await channel.send(f":regional_indicator_x: {str(video)} è stato rimosso dalla coda.")
            logger.debug(f"Removed from queue: {video.plain_text()}")
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
        del self.video_queue.list[start:end]
        await channel.send(f":regional_indicator_x: {end - start} video rimossi dalla coda.")
        logger.debug(f"Removed from queue {end - start} videos.")

    @command
    async def cmd_queue(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        if len(self.video_queue) == 0:
            await channel.send("**Video in coda:**\n"
                               "nessuno")
            return
        msg = "**Video in coda:**\n"
        for index, video in enumerate(self.video_queue.list[:10]):
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
        random.shuffle(self.video_queue.list)
        logger.info(f"The queue was shuffled by {author.name}#{author.discriminator}.")
        await channel.send("♠️ ♦️ ♣️ ♥️ Shuffle completo!")

    @command
    @requires_connected_voice_client
    async def cmd_clear(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        if len(self.video_queue) == 0:
            await channel.send("⚠ Non ci sono video in coda!")
            return
        # TODO
        raise NotImplementedError()
        logger.info(f"The queue was cleared by {author.name}#{author.discriminator}.")
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
        logger.info(f"Video play was forced by {author.name}#{author.discriminator}.")
        # Parse the parameter as URL
        url = re.match(r"(?:https?://|ytsearch[0-9]*:).*", " ".join(params[1:]).strip("<>"))
        if url is not None:
            # This is a url
            await self.add_video_from_url(url.group(0), enqueuer=author)
            await channel.send(f"✅ Video aggiunto alla coda.")
            logger.debug(f"Forced {url} as URL.")
            return
        # Parse the parameter as file
        file_path = os.path.join(os.path.join(os.path.curdir, "opusfiles"), " ".join(params[1:]))
        if os.path.exists(file_path):
            # This is a file
            await self.add_video_from_file(file=file_path, enqueuer=author)
            await channel.send(f"✅ Video aggiunto alla coda.")
            logger.debug(f"Forced {file_path} as file.")
            return
        file_path += ".opus"
        if os.path.exists(file_path):
            # This is a file
            await self.add_video_from_file(file=file_path, enqueuer=author)
            await channel.send(f"✅ Video aggiunto alla coda.")
            logger.debug(f"Forced {file_path} as file.")
            return
        # Search the parameter on youtube
        search = " ".join(params[1:])
        # This is a search
        await self.add_video_from_url(url=f"ytsearch:{search}", enqueuer=author)
        await channel.send(f"✅ Video aggiunto alla coda.")
        logger.debug(f"Forced ytsearch:{search} as YouTube search.")

    @command
    async def cmd_radiomessages(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        if not self.radio_messages_enabled:
            await channel.send("⚠ I messaggi radio sono stati disabilitati dall'amministratore del bot.")
            return
        if len(params) < 2:
            await channel.send("⚠ Sintassi del comando non valida.\n"
                               "Sintassi: `!radiomessages <on|off>`")
        else:
            if params[1].lower() == "on":
                self.radio_messages_next_in = self.radio_messages_every
            elif params[1].lower() == "off":
                self.radio_messages_next_in = math.inf
            else:
                await channel.send("⚠ Sintassi del comando non valida.\n"
                                   "Sintassi: `!radiomessages <on|off>`")
                return
        logger.info(f"Radio messages status to {'enabled' if self.radio_messages.next_in < math.inf else 'disabled'}.")
        await channel.send(f"📻 Messaggi radio **{'attivati' if self.radio_messages.next_in < math.inf else 'disattivati'}**.")

    @command
    @requires_connected_voice_client
    async def cmd_pause(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        for voice_client in self.voice_clients:
            if voice_client.is_playing():
                voice_client.pause()
                logger.debug(f"The audio stream was paused.")
                await channel.send(f"⏸ Riproduzione messa in pausa.\n"
                                   f"Riprendi con `!resume`.")

    @command
    @requires_connected_voice_client
    async def cmd_resume(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        for voice_client in self.voice_clients:
            if voice_client.is_paused():
                voice_client.resume()
                logger.debug(f"The audio stream was resumed.")
                await channel.send(f"⏯ Riproduzione ripresa.")


def process(users_connection=None):
    logger.info("Initializing the bot...")
    bot = RoyalDiscordBot()
    if users_connection is not None:
        logger.info("Initializing Telegram-Discord connection...")
        asyncio.ensure_future(bot.feed_pipe(users_connection))
    logger.info("Logging in...")
    loop.run_until_complete(bot.login(bot.token, bot=True))
    logger.info("Connecting...")
    loop.run_until_complete(bot.connect())
    logger.info("Now stopping...")
    loop.run_until_complete(bot.logout())


if __name__ == "__main__":
    process()
