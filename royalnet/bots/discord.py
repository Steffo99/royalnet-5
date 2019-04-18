import discord
import asyncio
import typing
import logging as _logging
import sys
from ..commands import NullCommand
from ..utils import asyncify, Call, Command, NetworkHandler
from ..error import UnregisteredError, NoneFoundError, TooManyFoundError, InvalidConfigError
from ..network import RoyalnetLink, Message, RequestSuccessful, RequestError
from ..database import Alchemy, relationshiplinkchain, DatabaseConfig
from ..audio import RoyalPCMFile, PlayMode, Playlist

loop = asyncio.get_event_loop()
log = _logging.getLogger(__name__)

# TODO: Load the opus library
if not discord.opus.is_loaded():
    log.error("Opus is not loaded. Weird behaviour might emerge.")


class DiscordBot:
    def __init__(self,
                 token: str,
                 master_server_uri: str,
                 master_server_secret: str,
                 commands: typing.List[typing.Type[Command]],
                 missing_command: typing.Type[Command] = NullCommand,
                 error_command: typing.Type[Command] = NullCommand,
                 database_config: typing.Optional[DatabaseConfig] = None):
        self.token = token
        # Generate the Alchemy database
        if database_config:
            self.alchemy = Alchemy(database_config.database_uri, required_tables)
            self.master_table = self.alchemy.__getattribute__(database_config.master_table.__name__)
            self.identity_table = self.alchemy.__getattribute__(database_config.identity_table.__name__)
            self.identity_column = self.identity_table.__getattribute__(self.identity_table, database_config.identity_column_name)
            self.identity_chain = relationshiplinkchain(self.master_table, self.identity_table)
        else:
            if required_tables:
                raise InvalidConfigError("Tables are required by the _commands, but Alchemy is not configured")
            self.alchemy = None
            self.master_table = None
            self.identity_table = None
            self.identity_column = None
            self.identity_chain = None
        # Create the PlayModes dictionary
        self.music_data: typing.Dict[discord.Guild, PlayMode] = {}

        # noinspection PyMethodParameters
        class DiscordCall(Call):
            interface_name = "discord"
            interface_obj = self
            interface_prefix = "!"

            alchemy = self.alchemy

            async def reply(call, text: str):
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
                    .replace("[/c]", "`")
                await call.channel.send(escaped_text)

            async def net_request(call, message: Message, destination: str):
                response = await self.network.request(message, destination)
                if isinstance(response, RequestError):
                    raise response.exc
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

        self.DiscordCall = DiscordCall

        # noinspection PyMethodParameters
        class DiscordClient(discord.Client):
            @staticmethod
            async def vc_connect_or_move(channel: discord.VoiceChannel):
                # Connect to voice chat
                try:
                    await channel.connect()
                except discord.errors.ClientException:
                    # Move to the selected channel, instead of connecting
                    # noinspection PyUnusedLocal
                    for voice_client in self.bot.voice_clients:
                        voice_client: discord.VoiceClient
                        if voice_client.guild != channel.guild:
                            continue
                        await voice_client.move_to(channel)
                # Create a music_data entry, if it doesn't exist; default is a Playlist
                if not self.music_data.get(channel.guild):
                    self.music_data[channel.guild] = Playlist()

            async def on_message(cli, message: discord.Message):
                text = message.content
                # Skip non-text messages
                if not text:
                    return
                # Find and clean parameters
                command_text, *parameters = text.split(" ")
                # Find the function
                try:
                    selected_command = self.commands[command_text]
                except KeyError:
                    # Skip inexistent _commands
                    selected_command = self.missing_command
                log.error(f"Running {selected_command}")
                # Call the command
                try:
                    return await self.DiscordCall(message.channel, selected_command, parameters, log,
                                                  message=message).run()
                except Exception as exc:
                    try:
                        return await self.DiscordCall(message.channel, self.error_command, parameters, log,
                                                      message=message,
                                                      exception_info=sys.exc_info(),
                                                      previous_command=selected_command).run()
                    except Exception as exc2:
                        log.error(f"Exception in error handler command: {exc2}")

        self.DiscordClient = DiscordClient
        self.bot = self.DiscordClient()

    def find_guild(self, identifier: typing.Union[str, int]) -> discord.Guild:
        """Find the Guild with the specified identifier. Names are case-insensitive."""
        if isinstance(identifier, str):
            all_guilds: typing.List[discord.Guild] = self.bot.guilds
            matching_channels: typing.List[discord.Guild] = []
            for guild in all_guilds:
                if guild.name.lower() == identifier.lower():
                    matching_channels.append(guild)
            if len(matching_channels) == 0:
                raise NoneFoundError("No channels were found")
            elif len(matching_channels) > 1:
                raise TooManyFoundError("Too many channels were found")
            return matching_channels[0]
        elif isinstance(identifier, int):
            return self.bot.get_guild(identifier)
        raise TypeError("Invalid identifier type, should be str or int")

    def find_channel(self,
                     identifier: typing.Union[str, int],
                     guild: typing.Optional[discord.Guild] = None) -> discord.abc.GuildChannel:
        """Find the GuildChannel with the specified identifier. Names are case-insensitive."""
        if isinstance(identifier, str):
            if guild is not None:
                all_channels = guild.channels
            else:
                all_channels: typing.List[discord.abc.GuildChannel] = self.bot.get_all_channels()
            matching_channels: typing.List[discord.abc.GuildChannel] = []
            for channel in all_channels:
                if not (isinstance(channel, discord.TextChannel)
                        or isinstance(channel, discord.VoiceChannel)
                        or isinstance(channel, discord.CategoryChannel)):
                    continue
                if channel.name.lower() == identifier.lower():
                    matching_channels.append(channel)
            if len(matching_channels) == 0:
                raise NoneFoundError("No channels were found")
            elif len(matching_channels) > 1:
                raise TooManyFoundError("Too many channels were found")
            return matching_channels[0]
        elif isinstance(identifier, int):
            channel: typing.List[discord.abc.GuildChannel] = self.bot.get_channel(identifier)
            if ((isinstance(channel, discord.TextChannel)
                 or isinstance(channel, discord.VoiceChannel)
                 or isinstance(channel, discord.CategoryChannel))
                and guild):
                assert channel.guild == guild
            return channel
        raise TypeError("Invalid identifier type, should be str or int")

    def find_voice_client(self, guild: discord.Guild):
        for voice_client in self.bot.voice_clients:
            voice_client: discord.VoiceClient
            if voice_client.guild == guild:
                return voice_client
        raise NoneFoundError("No voice clients found")

    async def add_to_music_data(self, url: str, guild: discord.Guild):
        """Add a file to the corresponding music_data object."""
        log.debug(f"Downloading {url} to add to music_data")
        files: typing.List[RoyalPCMFile] = await asyncify(RoyalPCMFile.create_from_url, url)
        guild_music_data = self.music_data[guild]
        for file in files:
            log.debug(f"Adding {file} to music_data")
            guild_music_data.add(file)
        if guild_music_data.now_playing is None:
            log.debug(f"Starting playback chain")
            await self.advance_music_data(guild)

    async def advance_music_data(self, guild: discord.Guild):
        """Try to play the next song, while it exists. Otherwise, just return."""
        guild_music_data = self.music_data[guild]
        voice_client = self.find_voice_client(guild)
        next_file: RoyalPCMFile = await guild_music_data.next()
        if next_file is None:
            log.debug(f"Ending playback chain")
            return

        def advance(error=None):
            log.debug(f"Deleting {next_file}")
            next_file.delete_audio_file()
            loop.create_task(self.advance_music_data(guild))

        log.debug(f"Creating AudioSource of {next_file}")
        next_source = next_file.create_audio_source()
        log.debug(f"Starting playback of {next_source}")
        voice_client.play(next_source, after=advance)

    async def run(self):
        await self.bot.login(self.token)
        await self.bot.connect()
        # TODO: how to stop?
