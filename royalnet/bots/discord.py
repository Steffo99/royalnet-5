import discord
import asyncio
import typing
import logging as _logging
from .generic import GenericBot
from ..commands import NullCommand
from ..utils import asyncify, Call, Command
from ..error import UnregisteredError, NoneFoundError, TooManyFoundError, InvalidConfigError
from ..network import Message, RoyalnetConfig
from ..database import DatabaseConfig
from ..audio import PlayMode, Playlist, RoyalPCMAudio

loop = asyncio.get_event_loop()
log = _logging.getLogger(__name__)

# TODO: Load the opus library
if not discord.opus.is_loaded():
    log.error("Opus is not loaded. Weird behaviour might emerge.")


class DiscordConfig:
    def __init__(self, token: str):
        self.token = token


class DiscordBot(GenericBot):
    interface_name = "discord"

    def _init_voice(self):
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
                escaped_text = text.replace("*", "\\*") \
                    .replace("_", "\\_") \
                    .replace("`", "\\`") \
                    .replace("[b]", "**") \
                    .replace("[/b]", "**") \
                    .replace("[i]", "_") \
                    .replace("[/i]", "_") \
                    .replace("[u]", "__") \
                    .replace("[/u]", "__") \
                    .replace("[c]", "`") \
                    .replace("[/c]", "`") \
                    .replace("[p]", "```") \
                    .replace("[/p]", "```")
                await call.channel.send(escaped_text)

            async def net_request(call, message: Message, destination: str):
                if self.network is None:
                    raise InvalidConfigError("Royalnet is not enabled on this bot")
                response: Message = await self.network.request(message, destination)
                response.raise_on_error()
                return response

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
        """Create a new DiscordClient class based on this DiscordBot."""
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
                """Find the Guild with the specified name. Case-insensitive.
                Will raise a NoneFoundError if no channels are found, or a TooManyFoundError if more than one is found."""
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
                """Find the TextChannel, VoiceChannel or CategoryChannel with the specified name. Case-insensitive.
                Guild is optional, but the method will raise a TooManyFoundError if none is specified and there is more than one channel with the same name.
                Will also raise a NoneFoundError if no channels are found."""
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
                """Find the VoiceClient belonging to a specific Guild.
                Raises a NoneFoundError if the Guild currently has no VoiceClient."""
                for voice_client in cli.voice_clients:
                    voice_client: discord.VoiceClient
                    if voice_client.guild == guild:
                        return voice_client
                raise NoneFoundError("No voice clients found")

        return DiscordClient

    def _init_client(self):
        """Create a bot instance."""
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
        log.debug(f"Logging in to Discord")
        await self.client.login(self._discord_config.token)
        log.debug(f"Connecting to Discord")
        await self.client.connect()
        # TODO: how to stop?

    async def add_to_music_data(self, audio_sources: typing.List[discord.AudioSource], guild: discord.Guild):
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
        await self.update_activity_with_source_title(next_source)
        if next_source is None:
            log.debug(f"Ending playback chain")
            return

        def advance(error=None):
            if error:
                raise Exception(f"Error while advancing music_data: {error}")
            loop.create_task(self.advance_music_data(guild))

        log.debug(f"Starting playback of {next_source}")
        voice_client.play(next_source, after=advance)

    async def update_activity_with_source_title(self, rpa: typing.Optional[RoyalPCMAudio] = None):
        if len(self.music_data) > 1:
            # Multiple guilds are using the bot, do not display anything
            log.debug(f"Updating current Activity: setting to None, as multiple guilds are using the bot")
            await self.client.change_presence(status=discord.Status.online)
            return
        if rpa is None:
            # No songs are playing now
            log.debug(f"Updating current Activity: setting to None, as nothing is currently being played")
            await self.client.change_presence(status=discord.Status.online)
            return
        log.debug(f"Updating current Activity: listening to {rpa.rpf.info.title}")
        await self.client.change_presence(activity=discord.Activity(name=rpa.rpf.info.title,
                                                                    type=discord.ActivityType.listening),
                                          status=discord.Status.online)
