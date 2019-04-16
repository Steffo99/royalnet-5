import discord
import asyncio
import typing
import logging as _logging
import sys
from ..commands import NullCommand
from ..utils import asyncify, Call, Command
from ..error import UnregisteredError, NoneFoundError, TooManyFoundError
from ..network import RoyalnetLink, Message, RequestSuccessful
from ..database import Alchemy, relationshiplinkchain
from ..audio import RoyalAudioFile

loop = asyncio.get_event_loop()
log = _logging.getLogger(__name__)

# TODO: Load the opus library
if not discord.opus.is_loaded():
    log.error("Opus is not loaded. Weird behaviour might emerge.")


class PlayMessage(Message):
    def __init__(self, url: str, channel_identifier: typing.Optional[typing.Union[int, str]] = None):
        self.url: str = url
        self.channel_identifier: typing.Optional[typing.Union[int, str]] = channel_identifier


class SummonMessage(Message):
    def __init__(self, channel_identifier: typing.Union[int, str],
                 guild_identifier: typing.Optional[typing.Union[int, str]]):
        self.channel_identifier = channel_identifier
        self.guild_identifier = guild_identifier


class DiscordBot:
    def __init__(self,
                 token: str,
                 master_server_uri: str,
                 master_server_secret: str,
                 commands: typing.List[typing.Type[Command]],
                 database_uri: str,
                 master_table,
                 identity_table,
                 identity_column_name: str,
                 missing_command: typing.Type[Command] = NullCommand,
                 error_command: typing.Type[Command] = NullCommand):
        self.token = token
        # Generate commands
        self.missing_command = missing_command
        self.error_command = error_command
        self.commands = {}
        required_tables = set()
        for command in commands:
            self.commands[f"!{command.command_name}"] = command
            required_tables = required_tables.union(command.require_alchemy_tables)
        # Generate the Alchemy database
        self.alchemy = Alchemy(database_uri, required_tables)
        self.master_table = self.alchemy.__getattribute__(master_table.__name__)
        self.identity_table = self.alchemy.__getattribute__(identity_table.__name__)
        self.identity_column = self.identity_table.__getattribute__(self.identity_table, identity_column_name)
        self.identity_chain = relationshiplinkchain(self.master_table, self.identity_table)
        # Connect to Royalnet
        self.network: RoyalnetLink = RoyalnetLink(master_server_uri, master_server_secret, "discord",
                                                  self.network_handler)
        loop.create_task(self.network.run())

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
                    # Skip inexistent commands
                    selected_command = self.missing_command
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

    def find_guild(self, identifier: typing.Union[str, int]):
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

    def find_channel(self, identifier: typing.Union[str, int], guild: typing.Optional[discord.Guild] = None):
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

    async def network_handler(self, message: Message) -> Message:
        """Handle a Royalnet request."""
        if isinstance(message, SummonMessage):
            return await self.nh_summon(message)
        elif isinstance(message, PlayMessage):
            return await self.nh_play(message)

    async def nh_summon(self, message: SummonMessage):
        """Handle a summon Royalnet request. That is, join a voice channel, or move to a different one if that is not possible."""
        channel = self.find_channel(message.channel_identifier)
        if not isinstance(channel, discord.VoiceChannel):
            raise NoneFoundError("Channel is not a voice channel")
        loop.create_task(self.bot.vc_connect_or_move(channel))
        return RequestSuccessful()

    async def nh_play(self, message: PlayMessage):
        """Handle a play Royalnet request. That is, add audio to a PlayMode."""
        raise

    async def run(self):
        await self.bot.login(self.token)
        await self.bot.connect()
        # TODO: how to stop?
