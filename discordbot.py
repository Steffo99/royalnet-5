import random
import re
# discord.py has a different name
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
import raven
import logging
import datetime
import coloredlogs
from utils import errors
import math
import enum
import requests

logging.getLogger().disabled = True
logger = logging.getLogger(__name__)
os.environ["COLOREDLOGS_LOG_FORMAT"] = "%(asctime)s %(levelname)s %(name)s %(message)s"
coloredlogs.install(level="DEBUG", logger=logger)

# Number emojis from zero (now playing) to ten
number_emojis = [":arrow_forward:",
                 ":one:",
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

# FFmpeg settings
ffmpeg_settings = {}

# Init the executor
executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)


class Succ:
    """All calls to this class return itself."""

    def __bool__(self):
        return False

    def __getattr__(self, attr):
        return Succ()

    def __call__(self, *args, **kwargs):
        return Succ()

    def __str__(self):
        return "succ"

    def __repr__(self):
        return "<Succ>"


class Video:
    def __init__(self, enqueuer: typing.Optional[discord.Member] = None):
        self.is_ready = False
        self.name = None
        self.enqueuer = enqueuer
        self.audio_source = None
        self.suggestion = None

    def __str__(self):
        if self.name is None:
            return "_Untitled_"
        return self.name

    def plain_text(self):
        """Title without formatting to be printed on terminals."""
        if self.name is None:
            return "Untitled"
        return self.name

    def database_text(self):
        """The text to be stored in the database for the stats. Usually the same as plain_text()."""
        if self.name is None:
            raise errors.VideoHasNoName()
        return self.name

    def __repr__(self):
        return f"<Video {self.name} ({'' if self.is_ready else 'not '}ready) added by {self.enqueuer}>"

    def ready_up(self):
        """Prepare the video for playback in some way. For example, download it."""
        raise NotImplementedError()

    def make_audio_source(self):
        """Create an AudioSource to be played through Discord, and store and return it."""
        raise NotImplementedError()

    def get_suggestion(self):
        """Set the next suggested video in the self.suggestion variable, to be used when the queue is in
        LoopMode.FOLLOW_SUGGESTION"""
        raise NotImplementedError()


class YoutubeDLVideo(Video):
    """A file sourcing from YoutubeDL."""

    def __init__(self, url, enqueuer: typing.Optional[discord.Member] = None, *, youtube_api_key: str = None):
        super().__init__(enqueuer)
        self.url = url
        self.info = None
        self.youtube_api_key = youtube_api_key

    def get_info(self):
        """Get info about the video."""
        if self.info:
            return
        logger.debug(f"Getting info on {self.url}...")
        with youtube_dl.YoutubeDL({"quiet": True,
                                   "ignoreerrors": True,
                                   "simulate": True}) as ytdl:
            data = ytdl.extract_info(url=self.url, download=False)
        if data is None:
            raise errors.VideoInfoExtractionFailed()
        if "entries" in data:
            raise errors.VideoIsPlaylist()
        self.info = data
        self.name = data.get("title")

    def __str__(self):
        if self.info is None:
            return f"`{self.url}`"
        return f"_{self.name}_"

    def plain_text(self):
        if self.info is None:
            return self.url
        if not self.name.isprintable():
            return self.url
        return self.name

    def get_filename(self):
        """Generate the filename of the video."""
        if self.info is None:
            raise errors.VideoInfoUnknown()
        return "./opusfiles/{}.opus".format(re.sub(r'[/\\?*"<>|!:]', "_", self.info.get("title", self.info["id"])))

    def ready_up(self):
        """Download the video."""
        # Skip download if it is already ready
        if self.is_ready:
            return
        # Retrieve info about the video
        self.get_info()
        # Check if the file to download already exists
        if os.path.exists(self.get_filename()):
            self.is_ready = True
            return
        # Download the file
        logger.info(f"Starting youtube_dl download of {repr(self)}")
        with youtube_dl.YoutubeDL({"noplaylist": True,
                                   "format": "best",
                                   "postprocessors": [{
                                       "key": 'FFmpegExtractAudio',
                                       "preferredcodec": 'opus'
                                   }],
                                   "outtmpl": self.get_filename(),
                                   "quiet": True}) as ytdl:
            ytdl.download([self.url])
        logger.info(f"Completed youtube_dl download of {repr(self)}")
        self.is_ready = True

    def make_audio_source(self):
        if not self.is_ready:
            raise errors.VideoIsNotReady()
        self.audio_source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(self.get_filename(), **ffmpeg_settings))
        return self.audio_source

    def get_suggestion(self):
        if self.suggestion is not None:
            return
        # Ensure the video has info
        self.get_info()
        # Ensure the video is from youtube
        if self.info["extractor"] != "youtube":
            # TODO: add more websites?
            self.suggestion = NotImplemented
        # Log the attempt
        logger.debug(f"Getting a suggestion for {self.url}...")
        # Check for the api key
        if self.youtube_api_key is None:
            raise errors.MissingAPIKeyError()
        # Request search data (costs 100 API units)
        r = requests.get("https://www.googleapis.com/youtube/v3/search?part=snippet", params={
            "part": "snippet",
            "type": "video",
            "key": self.youtube_api_key,
            "relatedToVideoId": self.info["id"]
        })
        r.raise_for_status()
        # Parse the request data
        j = r.json()
        # Find the suggested video
        if len(j["items"]) < 1:
            self.suggestion = ...
        first_video_id = j["items"][0]["id"]["videoId"]
        self.suggestion = YoutubeDLVideo(f"https://www.youtube.com/watch?v={first_video_id}",
                                         enqueuer=None,
                                         youtube_api_key=self.youtube_api_key)


class LoopMode(enum.Enum):
    NORMAL = enum.auto()
    LOOP_QUEUE = enum.auto()
    LOOP_SINGLE = enum.auto()
    FOLLOW_SUGGESTIONS = enum.auto()
    AUTO_SHUFFLE = enum.auto()
    LOOPING_SHUFFLE = enum.auto()


class VideoQueue:
    """The queue of videos to be played."""

    def __init__(self):
        self.list: typing.List[Video] = []
        self.loop_mode = LoopMode.NORMAL

    def __len__(self) -> int:
        return len(self.list)

    def __repr__(self) -> str:
        return f"<VideoQueue of length {len(self)} in mode {self.loop_mode}>"

    def add(self, video: Video, position: int = None) -> None:
        if position is None:
            self.list.append(video)
            return
        self.list.insert(position, video)

    def pop(self, index) -> Video:
        if self.loop_mode == LoopMode.FOLLOW_SUGGESTIONS:
            raise errors.LoopModeError("Can't pop items from a suggestion queue.")
        result = self[index]
        self.list.remove(result)
        return result

    def advance_queue(self):
        """Advance the queue to the next video."""
        del self[0]
    
    def next_video(self) -> typing.Optional[Video]:
        try:
            return self[1]
        except IndexError:
            return None

    def shuffle(self):
        part = self.list[1:]
        random.shuffle(part)
        part.insert(0, self.list[0])
        self.list = part

    def clear(self):
        self.list = []

    def find_video(self, name: str) -> typing.Optional[Video]:
        """Returns the first video with a certain name."""
        for video in self.list:
            if name in video.name:
                return video
        return None

    def not_ready_videos(self, limit: typing.Optional[int] = None):
        """Return the non-ready videos in the first limit positions of the queue."""
        video_list = []
        for video in (self[:limit]):
            if not video.is_ready:
                video_list.append(video)
        return video_list

    async def async_not_ready_videos(self, limit: typing.Optional[int] = None):
        """Return the non-ready videos in the first limit positions of the queue."""
        video_list = []
        full_list = await loop.run_in_executor(executor, functools.partial(self.__getitem__, slice(None, limit, None)))
        for video in full_list:
            if not video.is_ready:
                video_list.append(video)
        return video_list

    def __getitem__(self, index: typing.Union[int, slice]) -> typing.Union[Video, typing.Iterable]:
        """Get an enqueued element."""
        if isinstance(index, int):
            if self.loop_mode == LoopMode.NORMAL:
                return self.list[index]
            elif self.loop_mode == LoopMode.LOOP_QUEUE:
                if len(self.list) == 0:
                    raise IndexError()
                return self.list[index % len(self.list)]
            elif self.loop_mode == LoopMode.LOOP_SINGLE:
                if len(self.list) == 0:
                    raise IndexError()
                return self.list[0]
            elif self.loop_mode == LoopMode.FOLLOW_SUGGESTIONS:
                counter = index
                video = self.list[0]
                while counter > 0:
                    video.get_suggestion()
                    video = video.suggestion
                    counter -= 1
                return video
            elif self.loop_mode == LoopMode.AUTO_SHUFFLE:
                if index == 0:
                    return self.list[0]
                elif index >= len(self.list):
                    raise IndexError()
                number = random.randrange(1, len(self.list))
                return self.list[number]
            elif self.loop_mode == LoopMode.LOOPING_SHUFFLE:
                if index == 0:
                    return self.list[0]
                number = random.randrange(1, len(self.list))
                return self.list[number]
        else:
            # FIXME: won't work properly in multiple cases, but should work fine enough for now
            video_list = []
            if self.loop_mode == LoopMode.FOLLOW_SUGGESTIONS:
                try:
                    video = self.list[0]
                except IndexError:
                    return video_list
                while True:
                    if video is None:
                        break
                    video_list.append(video)
                    video = video.suggestion
            else:
                for i in range(len(self)):
                    video_list.append(self[i])
            return video_list[index]

    async def async_getitem(self, index):
        return await loop.run_in_executor(executor, functools.partial(self.__getitem__, index))

    def __delitem__(self, index: typing.Union[int, slice]):
        if isinstance(index, int):
            if self.loop_mode == LoopMode.LOOP_SINGLE:
                pass
            elif self.loop_mode == LoopMode.FOLLOW_SUGGESTIONS:
                if index != 0:
                    raise errors.LoopModeError("Deleting suggested videos different than the current one is impossible.")
                else:
                    video = self[0]
                    if video.suggestion is not None:
                        self.list.append(video.suggestion)
                    del self.list[0]
            del self.list[index]
        else:
            for i in range(index.start, index.stop, index.step):
                del self[i]


def escape(message: str):
    return message.replace("<", "&lt;").replace(">", "&gt;")


def command(func):
    """Decorator. Runs the function as a Discord command."""

    async def new_func(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str], *args,
                       **kwargs):
        if author is not None:
            self.sentry.user_context({
                "discord_id": author.id,
                "username": f"{author.name}#{author.discriminator}"
            })
        else:
            self.sentry.user_context({
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
            self.sentry.captureException(exc_info=ei)
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
        self.video_queue: VideoQueue = VideoQueue()
        self.load_config("config.ini")
        self.commands = {
            f"{self.command_prefix}ping": self.cmd_ping,
            f"{self.command_prefix}cv": self.cmd_cv,
            f"{self.command_prefix}summon": self.cmd_cv,
            f"{self.command_prefix}play": self.cmd_play,
            f"{self.command_prefix}alexaplay": self.cmd_play,
            f"{self.command_prefix}okgoogleplay": self.cmd_play,
            f"{self.command_prefix}heysiriplay": self.cmd_play,
            f"{self.command_prefix}p": self.cmd_play,
            f"{self.command_prefix}search": self.cmd_play,
            f"{self.command_prefix}file": self.cmd_play,
            f"{self.command_prefix}skip": self.cmd_skip,
            f"{self.command_prefix}s": self.cmd_skip,
            f"{self.command_prefix}next": self.cmd_skip,
            f"{self.command_prefix}remove": self.cmd_remove,
            f"{self.command_prefix}r": self.cmd_remove,
            f"{self.command_prefix}cancel": self.cmd_remove,
            f"{self.command_prefix}queue": self.cmd_queue,
            f"{self.command_prefix}q": self.cmd_queue,
            f"{self.command_prefix}shuffle": self.cmd_shuffle,
            f"{self.command_prefix}clear": self.cmd_clear,
            f"{self.command_prefix}register": self.cmd_register,
            f"{self.command_prefix}radiomessages": self.cmd_radiomessages,
            f"{self.command_prefix}yes": self.null,
            f"{self.command_prefix}no": self.null,
            f"{self.command_prefix}pause": self.cmd_pause,
            f"{self.command_prefix}resume": self.cmd_resume,
            f"{self.command_prefix}loop": self.cmd_mode,
            f"{self.command_prefix}l": self.cmd_mode,
            f"{self.command_prefix}mode": self.cmd_mode,
            f"{self.command_prefix}m": self.cmd_mode
        }
        if self.sentry_token:
            self.sentry = raven.Client(self.sentry_token,
                                       release=raven.fetch_git_sha(os.path.dirname(__file__)),
                                       install_logging_hook=False,
                                       hook_libraries=[])
        else:
            logger.warning("Sentry not set, ignoring all calls to it.")
            self.sentry = Succ()
        self.inactivity_timer = 0

    # noinspection PyAttributeOutsideInit
    def load_config(self, filename):
        # Init the config reader
        config = configparser.ConfigParser()
        config.read(filename)
        # Token
        try:
            self.token = config["Discord"]["bot_token"]
        except (KeyError, ValueError):
            raise errors.InvalidConfigError("Missing Discord bot token.")
        # Main channels, will be fully loaded when ready
        try:
            self.main_guild_id = int(config["Discord"]["server_id"])
            self.main_channel_id = int(config["Discord"]["main_channel"])
        except (KeyError, ValueError):
            raise errors.InvalidConfigError("Missing main guild and channel ids.")
        # Max enqueable video duration
        # Defined in the YoutubeDLVideo class
        # Max videos to predownload
        try:
            self.max_videos_to_predownload = int(config["Discord"]["video_cache_size"])
        except (KeyError, ValueError):
            logger.warning("Max videos to predownload is not set, setting it to infinity.")
            self.max_videos_to_predownload = None
        # Max time to ready a video
        try:
            self.max_video_ready_time = int(config["Discord"]["max_ready_time"])
        except (KeyError, ValueError):
            logger.warning("Max time to ready a video is not set, setting it to infinity. ")
            self.max_video_ready_time = math.inf
        # Radio messages
        try:
            if config["Discord"]["radio_messages_enabled"] == "True":
                self.radio_messages = ["https://www.youtube.com/watch?v=3-yeK1Ck4yk",
                                       "https://youtu.be/YcR7du_A1Vc",
                                       "https://clyp.it/byg3i52l"]
                try:
                    self.radio_messages_every = int(config["Discord"]["radio_messages_every"])
                    self.radio_messages_next_in = self.radio_messages_every
                except (KeyError, ValueError):
                    logger.warning("Radio messages config error, disabling them.")
                    self.radio_messages = []
                    self.radio_messages_every = math.inf
                    self.radio_messages_next_in = math.inf
            else:
                logger.info("Radio messages are force-disabled.")
                self.radio_messages = []
                self.radio_messages_every = math.inf
                self.radio_messages_next_in = math.inf
        except (KeyError, ValueError):
            logger.warning("Radio messages config error, disabling them.")
            self.radio_messages = []
            self.radio_messages_every = math.inf
            self.radio_messages_next_in = math.inf
        # Activity reporting
        try:
            self.activity_report_sample_time = int(config["Discord"]["activityreport_sample_time"])
        except (KeyError, ValueError):
            logger.warning("Activity reporting config error, disabling it.")
            self.activity_report_sample_time = math.inf
        # Sentry error reporting
        try:
            self.sentry_token = config["Sentry"]["token"]
        except (KeyError, ValueError):
            logger.warning("Sentry client config error, disabling it.")
            self.sentry_token = None
        # Easter eggs
        try:
            if config["Discord"]["song_text_easter_eggs_enabled"] == "True":
                self.song_text_easter_eggs = {
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
                    "eurobeat": ":arrow_forward: Nemesis approva la scelta di {song}. Ben fatto, amico.",
                    "k/da": ":arrow_forward: Che noia...\n"
                            "Non ci si può nemmeno divertire con {song} che c'è qualcuno che se ne lamenta.\n"
                            "La prossima volta, metti qualcosa di diverso, per piacere.",
                    "youtube rewind": ":arrow_forward: Perchè ti vuoi così male?"
                                      " Sigh, ascolta, discutere con te è inutile."
                                      " Ti lascio qui {song}. Richiamami quando sarà tutto finito."
                }
            else:
                self.song_text_easter_eggs = {}
        except (KeyError, ValueError):
            logger.warning("Song text easter egg information not found, defaulting to disabled.")
            self.song_text_easter_eggs = {}
        # Discord command prefix
        try:
            self.command_prefix = config["Discord"]["command_prefix"]
        except (KeyError, ValueError):
            logger.warning("Command prefix not set, defaulting to '!'.")
            self.command_prefix = "!"
        # Youtube API Key
        try:
            self.youtube_api_key = config["YouTube"]["youtube_data_api_key"]
        except (KeyError, ValueError):
            logger.warning("Youtube API key not set, disabling suggestion mode.")
            self.youtube_api_key = None

    # noinspection PyAsyncCall
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
        asyncio.ensure_future(self.activity_task())

    async def on_message(self, message: discord.Message):
        if message.channel != self.main_channel or message.author.bot:
            return
        self.sentry.user_context({
            "discord": {
                "discord_id": message.author.id,
                "name": message.author.name,
                "discriminator": message.author.discriminator
            }
        })
        if not message.content.startswith(self.command_prefix):
            await message.channel.send(f"⚠️ In questa chat sono consentiti solo comandi per il bot.\n"
                                       f"Riinvia il tuo messaggio in un altro canale!")
            await message.delete()
            return
        data = message.content.split(" ")
        if data[0] not in self.commands:
            await message.channel.send("⚠️ Comando non riconosciuto.")
            return
        logger.debug(f"Received command: {message.content}")
        self.sentry.extra_context({
            "command": data[0],
            "message": message
        })
        self.inactivity_timer = 3600
        await self.commands[data[0]](channel=message.channel,
                                     author=message.author,
                                     params=data)

    async def on_error(self, event_method, *args, **kwargs):
        ei = sys.exc_info()
        logger.critical(f"Critical error: {repr(ei)}")
        # noinspection PyBroadException
        try:
            await self.main_channel.send(f"☢️ **ERRORE CRITICO NELL'EVENTO** `{event_method}`!\n"
                                         f"Il bot si è chiuso e si dovrebbe riavviare entro qualche minuto.\n"
                                         f"Una segnalazione di errore è stata automaticamente mandata a Steffo.\n\n"
                                         f"Dettagli dell'errore:\n"
                                         f"```python\n"
                                         f"{repr(ei)}\n"
                                         f"```")
            await self.change_presence(status=discord.Status.invisible)
            await self.close()
        except Exception:
            logger.error(f"Double critical error: {sys.exc_info()}")
        loop.stop()
        self.sentry.captureException(exc_info=ei)
        exit(1)

    async def feed_pipe(self, connection):
        await self.wait_until_ready()
        while True:
            msg = await loop.run_in_executor(executor, connection.recv)
            logger.debug(f"Received from the Telegram-Discord pipe: {msg}")
            full_cv = (msg == "get cv full")
            if msg.startswith("get cv"):
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
                        if not full_cv and channel == 0 and len(member.roles) < 2:
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
                                        message += f" ({escape(member.activity.state)}" \
                                            f" | {escape(member.activity.details)})"
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
        if self.activity_report_sample_time == math.inf:
            return
        while True:
            await self.create_activityreport()
            logger.debug(f"Waiting {self.activity_report_sample_time} seconds before the next record.")
            await asyncio.sleep(self.activity_report_sample_time)

    # noinspection PyUnusedLocal
    @command
    async def null(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        pass

    # noinspection PyUnusedLocal
    @command
    async def cmd_ping(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        await channel.send(f"Pong!")

    # noinspection PyUnusedLocal
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
            await channel.send("⚠️ Il tuo account Discord è già collegato a un account RYG "
                               "o l'account RYG che hai specificato è già collegato a un account Discord.")
            return
        session.add(d)
        session.commit()
        session.close()
        await channel.send("✅ Sincronizzazione completata!")

    # noinspection PyUnusedLocal
    @command
    async def cmd_cv(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        await channel.send("⚠️ discord.py è stato aggiornato e non è più compatibile con questa versione del bot. La musica non sarà disponibile fino alla release di **Royalnet Unity**...")

    # noinspection PyUnusedLocal
    @command
    @requires_connected_voice_client
    async def cmd_play(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        await channel.send("⚠️ discord.py è stato aggiornato e non è più compatibile con questa versione del bot. La musica non sarà disponibile fino alla release di **Royalnet Unity**...")

    # noinspection PyUnusedLocal
    @command
    @requires_connected_voice_client
    async def cmd_skip(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        await channel.send("⚠️ discord.py è stato aggiornato e non è più compatibile con questa versione del bot. La musica non sarà disponibile fino alla release di **Royalnet Unity**...")

    # noinspection PyUnusedLocal
    @command
    @requires_connected_voice_client
    async def cmd_remove(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        await channel.send("⚠️ discord.py è stato aggiornato e non è più compatibile con questa versione del bot. La musica non sarà disponibile fino alla release di **Royalnet Unity**...")

    # noinspection PyUnusedLocal
    @command
    async def cmd_queue(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        await channel.send("⚠️ discord.py è stato aggiornato e non è più compatibile con questa versione del bot. La musica non sarà disponibile fino alla release di **Royalnet Unity**...")

    # noinspection PyUnusedLocal
    @command
    @requires_connected_voice_client
    async def cmd_shuffle(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        await channel.send("⚠️ discord.py è stato aggiornato e non è più compatibile con questa versione del bot. La musica non sarà disponibile fino alla release di **Royalnet Unity**...")

    # noinspection PyUnusedLocal
    @command
    @requires_connected_voice_client
    async def cmd_clear(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        await channel.send("⚠️ discord.py è stato aggiornato e non è più compatibile con questa versione del bot. La musica non sarà disponibile fino alla release di **Royalnet Unity**...")

    # noinspection PyUnusedLocal
    @command
    async def cmd_radiomessages(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        await channel.send("⚠️ discord.py è stato aggiornato e non è più compatibile con questa versione del bot. La musica non sarà disponibile fino alla release di **Royalnet Unity**...")

    # noinspection PyUnusedLocal
    @command
    @requires_connected_voice_client
    async def cmd_pause(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        await channel.send("⚠️ discord.py è stato aggiornato e non è più compatibile con questa versione del bot. La musica non sarà disponibile fino alla release di **Royalnet Unity**...")

    # noinspection PyUnusedLocal
    @command
    @requires_connected_voice_client
    async def cmd_resume(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        await channel.send("⚠️ discord.py è stato aggiornato e non è più compatibile con questa versione del bot. La musica non sarà disponibile fino alla release di **Royalnet Unity**...")

    # noinspection PyUnusedLocal
    @command
    @requires_connected_voice_client
    async def cmd_mode(self, channel: discord.TextChannel, author: discord.Member, params: typing.List[str]):
        await channel.send("⚠️ discord.py è stato aggiornato e non è più compatibile con questa versione del bot. La musica non sarà disponibile fino alla release di **Royalnet Unity**...")


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
    loop.run_until_complete(bot.main_channel.send("ℹ️ Spegnimento bot in corso..."))
    loop.run_until_complete(bot.logout())


if __name__ == "__main__":
    process()
