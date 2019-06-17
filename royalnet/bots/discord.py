import discord
import asyncio
import typing
import logging as _logging
from .generic import GenericBot
from ..commands import NullCommand
from ..utils import asyncify, Call, Command, discord_escape
from ..error import UnregisteredError, NoneFoundError, TooManyFoundError, InvalidConfigError, RoyalnetResponseError
from ..network import RoyalnetConfig, Request, ResponseSuccess, ResponseError
from ..database import DatabaseConfig
from ..audio import PlayMode, Playlist, RoyalPCMAudio

log = _logging.getLogger(__name__)

# TODO: Load the opus library
if not discord.opus.is_loaded():
    log.error("Opus is not loaded. Weird behaviour might emerge.")


class DiscordConfig:
    """The specific configuration to be used for :py:class:`royalnet.bots.DiscordBot`."""
    def __init__(self, token: str):
        self.token = token


class DiscordBot(GenericBot):
    """A bot that connects to `Discord <https://discordapp.com/>`_."""

    interface_name = "discord"

    def _init_voice(self):
        """Initialize the variables needed for the connection to voice chat."""
        log.debug(f"Creating music_data dict")
        self.music_data: typing.Dict[discord.Guild, PlayMode] = {}

    def _call_factory(self) -> typing.Type[Call]:
        log.debug(f"Creating DiscordCall")

        # noinspection PyMethodParameters
        class DiscordCall(Call):
            interface_name = self.interface_name
            interface_obj = self
            interface_prefix = "!"

            alchemy = self.alchemy

            async def reply(call, text: str):
                # TODO: don't escape characters inside [c][/c] blocks
                await call.channel.send(discord_escape(text))

            async def net_request(call, request: Request, destination: str) -> dict:
                if self.network is None:
                    raise InvalidConfigError("Royalnet is not enabled on this bot")
                response_dict: dict = await self.network.request(request.to_dict(), destination)
                if "type" not in response_dict:
                    raise RoyalnetResponseError("Response is missing a type")
                elif response_dict["type"] == "ResponseSuccess":
                    response: typing.Union[ResponseSuccess, ResponseError] = ResponseSuccess.from_dict(response_dict)
                elif response_dict["type"] == "ResponseError":
                    response = ResponseError.from_dict(response_dict)
                else:
                    raise RoyalnetResponseError("Response type is unknown")
                response.raise_on_error()
                return response.data

            async def get_author(call, error_if_none=False):
                message: discord.Message = call.kwargs["message"]
                user: discord.Member = message.author
                query = call.session.query(self.master_table)
                for link in self.identity_chain:
                    query = query.join(link.mapper.class_)
                query = query.filter(self.identity_column == user.id)
                result = await asyncify(query.one_or_none)
                if result is None and error_if_none:
                    raise UnregisteredError("Author is not registered")
                return result

        return DiscordCall

    def _bot_factory(self) -> typing.Type[discord.Client]:
        """Create a custom DiscordClient class inheriting from :py:class:`discord.Client`."""
        log.debug(f"Creating DiscordClient")

        # noinspection PyMethodParameters
        class DiscordClient(discord.Client):
            async def vc_connect_or_move(cli, channel: discord.VoiceChannel):
                # Connect to voice chat
                try:
                    await channel.connect()
                    log.debug(f"Connecting to Voice in {channel}")
                except discord.errors.ClientException:
                    # Move to the selected channel, instead of connecting
                    # noinspection PyUnusedLocal
                    for voice_client in cli.voice_clients:
                        voice_client: discord.VoiceClient
                        if voice_client.guild != channel.guild:
                            continue
                        await voice_client.move_to(channel)
                        log.debug(f"Moved {voice_client} to {channel}")
                # Create a music_data entry, if it doesn't exist; default is a Playlist
                if not self.music_data.get(channel.guild):
                    log.debug(f"Creating music_data for {channel.guild}")
                    self.music_data[channel.guild] = Playlist()

            @staticmethod
            async def on_message(message: discord.Message):
                text = message.content
                # Skip non-text messages
                if not text:
                    return
                # Skip non-command updates
                if not text.startswith(self.command_prefix):
                    return
                # Skip bot messages
                author: typing.Union[discord.User] = message.author
                if author.bot:
                    return
                # Find and clean parameters
                command_text, *parameters = text.split(" ")
                # Don't use a case-sensitive command name
                command_name = command_text.lower()
                # Call the command
                await self.call(command_name, message.channel, parameters, message=message)

            async def on_ready(cli):
                log.debug("Connection successful, client is ready")
                await cli.change_presence(status=discord.Status.online)

            def find_guild_by_name(cli, name: str) -> discord.Guild:
                """Find the :py:class:`discord.Guild` with the specified name. Case-insensitive.

                Raises:
                     :py:exc:`NoneFoundError` if no channels are found.
                     :py:exc:`TooManyFoundError` if more than one is found."""
                all_guilds: typing.List[discord.Guild] = cli.guilds
                matching_channels: typing.List[discord.Guild] = []
                for guild in all_guilds:
                    if guild.name.lower() == name.lower():
                        matching_channels.append(guild)
                if len(matching_channels) == 0:
                    raise NoneFoundError("No channels were found")
                elif len(matching_channels) > 1:
                    raise TooManyFoundError("Too many channels were found")
                return matching_channels[0]

            def find_channel_by_name(cli,
                                     name: str,
                                     guild: typing.Optional[discord.Guild] = None) -> discord.abc.GuildChannel:
                """Find the :py:class:`TextChannel`, :py:class:`VoiceChannel` or :py:class:`CategoryChannel` with the specified name. Case-insensitive.
                Guild is optional, but the method will raise a :py:exc:`TooManyFoundError` if none is specified and there is more than one channel with the same name.
                Will also raise a :py:exc:`NoneFoundError` if no channels are found."""
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
                if len(matching_channels) == 0:
                    raise NoneFoundError("No channels were found")
                elif len(matching_channels) > 1:
                    raise TooManyFoundError("Too many channels were found")
                return matching_channels[0]

            def find_voice_client_by_guild(cli, guild: discord.Guild):
                """Find the :py:class:`discord.VoiceClient` belonging to a specific :py:class:`discord.Guild`.

                Raises:
                     :py:exc:`NoneFoundError` if the :py:class:`discord.Guild` currently has no :py:class:`discord.VoiceClient`."""
                for voice_client in cli.voice_clients:
                    if voice_client.guild == guild:
                        return voice_client
                raise NoneFoundError("No voice clients found")

        return DiscordClient

    def _init_client(self):
        """Create an instance of the DiscordClient class created in :py:func:`royalnet.bots.DiscordBot._bot_factory`."""
        log.debug(f"Creating DiscordClient instance")
        self._Client = self._bot_factory()
        self.client = self._Client()

    def __init__(self, *,
                 discord_config: DiscordConfig,
                 royalnet_config: typing.Optional[RoyalnetConfig] = None,
                 database_config: typing.Optional[DatabaseConfig] = None,
                 command_prefix: str = "!",
                 commands: typing.List[typing.Type[Command]] = None,
                 missing_command: typing.Type[Command] = NullCommand,
                 error_command: typing.Type[Command] = NullCommand):
        super().__init__(royalnet_config=royalnet_config,
                         database_config=database_config,
                         command_prefix=command_prefix,
                         commands=commands,
                         missing_command=missing_command,
                         error_command=error_command)
        self._discord_config = discord_config
        self._init_client()
        self._init_voice()

    async def run(self):
        """Login to Discord, then run the bot."""
        log.debug(f"Logging in to Discord")
        await self.client.login(self._discord_config.token)
        log.debug(f"Connecting to Discord")
        await self.client.connect()
        # TODO: how to stop?

    async def add_to_music_data(self, audio_sources: typing.List[RoyalPCMAudio], guild: discord.Guild):
        """Add a file to the corresponding music_data object."""
        guild_music_data = self.music_data[guild]
        for audio_source in audio_sources:
            log.debug(f"Adding {audio_source} to music_data")
            guild_music_data.add(audio_source)
        if guild_music_data.now_playing is None:
            await self.advance_music_data(guild)

    async def advance_music_data(self, guild: discord.Guild):
        """Try to play the next song, while it exists. Otherwise, just return."""
        guild_music_data = self.music_data[guild]
        voice_client = self.client.find_voice_client_by_guild(guild)
        next_source: RoyalPCMAudio = await guild_music_data.next()
        await self.update_activity_with_source_title()
        if next_source is None:
            log.debug(f"Ending playback chain")
            return

        def advance(error=None):
            if error:
                raise Exception(f"Error while advancing music_data: {error}")
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
        # FIXME: PyCharm faulty inspection?
        # noinspection PyUnresolvedReferences
        play_mode: PlayMode = list(self.music_data.items())[0][1]
        now_playing = play_mode.now_playing
        if now_playing is None:
            # No songs are playing now
            log.debug(f"Updating current Activity: setting to None, as nothing is currently being played")
            await self.client.change_presence(status=discord.Status.online)
            return
        log.debug(f"Updating current Activity: listening to {now_playing.rpf.info.title}")
        await self.client.change_presence(activity=discord.Activity(name=now_playing.rpf.info.title,
                                                                    type=discord.ActivityType.listening),
                                          status=discord.Status.online)
