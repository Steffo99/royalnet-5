import discord
import sentry_sdk
import logging as _logging
import asyncio
from .generic import GenericBot
from ..utils import *
from ..error import *
from ..audio import *
from ..commands import *

log = _logging.getLogger(__name__)

# TODO: Load the opus library
if not discord.opus.is_loaded():
    log.error("Opus is not loaded. Weird behaviour might emerge.")


class MusicData:
    def __init__(self):
        self.playmode: playmodes.PlayMode = playmodes.Playlist()
        self.voice_client: typing.Optional[discord.VoiceClient] = None

    def queue_preview(self):
        return self.playmode.queue_preview()


class DiscordBot(GenericBot):
    """A bot that connects to `Discord <https://discordapp.com/>`_."""
    interface_name = "discord"

    def _init_voice(self):
        """Initialize the variables needed for the connection to voice chat."""
        log.debug(f"Creating music_data dict")
        self.music_data: typing.Dict[discord.Guild, MusicData] = {}

    def _interface_factory(self) -> typing.Type[CommandInterface]:
        # noinspection PyPep8Naming
        GenericInterface = super()._interface_factory()

        # noinspection PyMethodParameters,PyAbstractClass
        class DiscordInterface(GenericInterface):
            name = self.interface_name
            prefix = "!"

        return DiscordInterface

    def _data_factory(self) -> typing.Type[CommandData]:
        # noinspection PyMethodParameters,PyAbstractClass
        class DiscordData(CommandData):
            def __init__(data, interface: CommandInterface, message: discord.Message):
                super().__init__(interface)
                data.message = message

            async def reply(data, text: str):
                await data.message.channel.send(discord_escape(text))

            async def get_author(data, error_if_none=False):
                user: discord.Member = data.message.author
                query = data.session.query(self.master_table)
                for link in self.identity_chain:
                    query = query.join(link.mapper.class_)
                query = query.filter(self.identity_column == user.id)
                result = await asyncify(query.one_or_none)
                if result is None and error_if_none:
                    raise CommandError("You must be registered to use this command.")
                return result

            async def delete_invoking(data, error_if_unavailable=False):
                await data.message.delete()

        return DiscordData

    def _bot_factory(self) -> typing.Type[discord.Client]:
        """Create a custom DiscordClient class inheriting from :py:class:`discord.Client`."""
        log.debug(f"Creating DiscordClient")

        # noinspection PyMethodParameters
        class DiscordClient(discord.Client):
            async def vc_connect_or_move(cli, channel: discord.VoiceChannel):
                music_data = self.music_data.get(channel.guild)
                if music_data is None:
                    # Create a MusicData object
                    music_data = MusicData()
                    self.music_data[channel.guild] = music_data
                    # Connect to voice
                    log.debug(f"Connecting to Voice in {channel}")
                    try:
                        music_data.voice_client = await channel.connect(reconnect=False, timeout=10)
                    except Exception:
                        log.warning(f"Failed to connect to Voice in {channel}")
                        del self.music_data[channel.guild]
                        raise
                    else:
                        log.debug(f"Connected to Voice in {channel}")
                else:
                    if music_data.voice_client is None:
                        # TODO: change exception type
                        raise Exception("Another connection attempt is already in progress.")
                    # Try to move to a different channel
                    voice_client = music_data.voice_client
                    log.debug(f"Moving {voice_client} to {channel}")
                    await voice_client.move_to(channel)
                    log.debug(f"Moved {voice_client} to {channel}")

            async def on_message(cli, message: discord.Message):
                self.loop.create_task(cli._handle_message(message))

            async def _handle_message(cli, message: discord.Message):
                text = message.content
                # Skip non-text messages
                if not text:
                    return
                # Skip non-command updates
                if not text.startswith("!"):
                    return
                # Skip bot messages
                author: typing.Union[discord.User] = message.author
                if author.bot:
                    return
                # Find and clean parameters
                command_text, *parameters = text.split(" ")
                # Don't use a case-sensitive command name
                command_name = command_text.lower()
                # Find the command
                try:
                    command = self.commands[command_name]
                except KeyError:
                    # Skip the message
                    return
                # Prepare data
                data = self._Data(interface=command.interface, message=message)
                # Call the command
                log.debug(f"Calling command '{command.name}'")
                with message.channel.typing():
                    # Run the command
                    try:
                        await command.run(CommandArgs(parameters), data)
                    except InvalidInputError as e:
                        await data.reply(f":warning: {e.message}\n"
                                         f"Syntax: [c]/{command.name} {command.syntax}[/c]")
                    except UnsupportedError as e:
                        await data.reply(f":warning: {e.message}")
                    except CommandError as e:
                        await data.reply(f":warning: {e.message}")
                    except Exception as e:
                        sentry_sdk.capture_exception(e)
                        error_message = f"🦀 [b]{e.__class__.__name__}[/b] 🦀\n"
                        error_message += '\n'.join(e.args)
                        await data.reply(error_message)
                # Close the data session
                await data.session_close()

            async def on_connect(cli):
                log.debug("Connected to Discord")

            async def on_disconnect(cli):
                log.error("Disconnected from Discord!")

            async def on_ready(cli) -> None:
                log.debug("Connection successful, client is ready")
                await cli.change_presence(status=discord.Status.online)

            def find_guild_by_name(cli, name: str) -> typing.List[discord.Guild]:
                """Find the :py:class:`discord.Guild` with the specified name (case insensitive)."""
                all_guilds: typing.List[discord.Guild] = cli.guilds
                matching_channels: typing.List[discord.Guild] = []
                for guild in all_guilds:
                    if guild.name.lower() == name.lower():
                        matching_channels.append(guild)
                return matching_channels

            def find_channel_by_name(cli,
                                     name: str,
                                     guild: typing.Optional[discord.Guild] = None) -> typing.List[discord.abc.GuildChannel]:
                """Find the :py:class:`TextChannel`, :py:class:`VoiceChannel` or :py:class:`CategoryChannel` with the
                specified name (case insensitive).

                You can specify a guild to only find channels in that specific guild."""
                if guild is not None:
                    all_channels = guild.channels
                else:
                    all_channels: typing.List[discord.abc.GuildChannel] = cli.get_all_channels()
                matching_channels: typing.List[discord.abc.GuildChannel] = []
                for channel in all_channels:
                    if not (isinstance(channel, discord.TextChannel)
                            or isinstance(channel, discord.VoiceChannel)
                            or isinstance(channel, discord.CategoryChannel)):
                        continue
                    if channel.name.lower() == name.lower():
                        matching_channels.append(channel)
                return matching_channels

            def find_voice_client_by_guild(cli, guild: discord.Guild) -> typing.Optional[discord.VoiceClient]:
                """Find the :py:class:`discord.VoiceClient` belonging to a specific :py:class:`discord.Guild`."""
                for voice_client in cli.voice_clients:
                    if voice_client.guild == guild:
                        return voice_client
                return None

        return DiscordClient

    def _init_client(self):
        """Create an instance of the DiscordClient class created in :py:func:`royalnet.bots.DiscordBot._bot_factory`."""
        log.debug(f"Creating DiscordClient instance")
        self._Client = self._bot_factory()
        self.client = self._Client()

    def _initialize(self):
        super()._initialize()
        self._init_client()
        self._init_voice()

    async def run(self):
        """Login to Discord, then run the bot."""
        if not self.initialized:
            self._initialize()
        log.debug("Getting Discord secret")
        token = self.get_secret("discord")
        log.info(f"Logging in to Discord")
        await self.client.login(token)
        log.info(f"Connecting to Discord")
        await self.client.connect()

    async def add_to_music_data(self, dfiles: typing.List[YtdlDiscord], guild: discord.Guild):
        """Add a list of :py:class:`royalnet.audio.YtdlDiscord` to the corresponding music_data object."""
        guild_music_data = self.music_data[guild]
        for dfile in dfiles:
            log.debug(f"Adding {dfile} to music_data")
            await asyncify(dfile.ready_up)
            guild_music_data.playmode.add(dfile)
        if guild_music_data.playmode.now_playing is None:
            await self.advance_music_data(guild)

    async def advance_music_data(self, guild: discord.Guild):
        """Try to play the next song, while it exists. Otherwise, just return."""
        guild_music_data = self.music_data[guild]
        voice_client: discord.VoiceClient = self.client.find_voice_client_by_guild(guild)
        next_source: discord.AudioSource = await guild_music_data.playmode.next()
        await self.update_activity_with_source_title()
        if next_source is None:
            log.debug(f"Ending playback chain")
            return

        def advance(error=None):
            if error:
                voice_client.disconnect(force=True)
                log.error(f"Error while advancing music_data: {error}")
                return
            self.loop.create_task(self.advance_music_data(guild))

        log.debug(f"Starting playback of {next_source}")
        voice_client.play(next_source, after=advance)

    async def update_activity_with_source_title(self):
        """Change the bot's presence (using :py:func:`discord.Client.change_presence`) to match the current listening status.

        If multiple guilds are using the bot, the bot will always have an empty presence."""
        if len(self.music_data) != 1:
            # Multiple guilds are using the bot, do not display anything
            log.debug(f"Updating current Activity: setting to None, as multiple guilds are using the bot")
            await self.client.change_presence(status=discord.Status.online)
            return
        play_mode: playmodes.PlayMode = self.music_data[list(self.music_data)[0]].playmode
        now_playing = play_mode.now_playing
        if now_playing is None:
            # No songs are playing now
            log.debug(f"Updating current Activity: setting to None, as nothing is currently being played")
            await self.client.change_presence(status=discord.Status.online)
            return
        log.debug(f"Updating current Activity: listening to {now_playing.info.title}")
        await self.client.change_presence(activity=discord.Activity(name=now_playing.info.title,
                                                                    type=discord.ActivityType.listening),
                                          status=discord.Status.online)
