import logging
import asyncio
from typing import Type, Optional, List, Callable, Union
from royalnet.commands import Command, CommandInterface, CommandData, CommandArgs, CommandError, InvalidInputError, \
                              UnsupportedError
from royalnet.utils import asyncify
from .escape import escape
from ..serf import Serf

try:
    import discord
except ImportError:
    discord = None

try:
    from sqlalchemy.orm.session import Session
    from ..alchemyconfig import AlchemyConfig
except ImportError:
    Session = None
    AlchemyConfig = None

try:
    from royalnet.herald import Config as HeraldConfig
except ImportError:
    HeraldConfig = None

log = logging.getLogger(__name__)


class DiscordSerf(Serf):
    """A :class:`Serf` that connects to `Discord <https://discordapp.com/>`_ as a bot."""
    interface_name = "discord"

    def __init__(self, *,
                 alchemy_config: Optional[AlchemyConfig] = None,
                 commands: List[Type[Command]] = None,
                 network_config: Optional[HeraldConfig] = None,
                 secrets_name: str = "__default__"):
        if discord is None:
            raise ImportError("'discord' extra is not installed")

        super().__init__(alchemy_config=alchemy_config,
                         commands=commands,
                         network_config=network_config,
                         secrets_name=secrets_name)

    def _interface_factory(self) -> Type[CommandInterface]:
        # noinspection PyPep8Naming
        GenericInterface = super().interface_factory()

        # noinspection PyMethodParameters,PyAbstractClass
        class DiscordInterface(GenericInterface):
            name = self.interface_name
            prefix = "!"

        return DiscordInterface

    def _data_factory(self) -> Type[CommandData]:
        # noinspection PyMethodParameters,PyAbstractClass
        class DiscordData(CommandData):
            def __init__(data, interface: CommandInterface, session, message: discord.Message):
                super().__init__(interface=interface, session=session)
                data.message = message

            async def reply(data, text: str):
                await data.message.channel.send(escape(text))

            async def get_author(data, error_if_none=False):
                user: discord.Member = data.message.author
                query = data.session.query(self._master_table)
                for link in self._identity_chain:
                    query = query.join(link.mapper.class_)
                query = query.filter(self._identity_column == user.id)
                result = await asyncify(query.one_or_none)
                if result is None and error_if_none:
                    raise CommandError("You must be registered to use this command.")
                return result

            async def delete_invoking(data, error_if_unavailable=False):
                await data.message.delete()

        return DiscordData

    async def handle_message(self, message: discord.Message):
        """Handle a Discord message by calling a command if appropriate."""
        text = message.content
        # Skip non-text messages
        if not text:
            return
        # Skip non-command updates
        if not text.startswith("!"):
            return
        # Skip bot messages
        author: Union[discord.User] = message.author
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
        # Call the command
        log.debug(f"Calling command '{command.name}'")
        with message.channel.typing():
            # Open an alchemy session, if available
            if self.alchemy is not None:
                session = await asyncify(self.alchemy.Session)
            else:
                session = None
            # Prepare data
            data = self.Data(interface=command.interface, session=session, message=message)
            try:
                # Run the command
                await command.run(CommandArgs(parameters), data)
            except InvalidInputError as e:
                await data.reply(f":warning: {e.message}\n"
                                 f"Syntax: [c]/{command.name} {command.syntax}[/c]")
            except UnsupportedError as e:
                await data.reply(f":warning: {e.message}")
            except CommandError as e:
                await data.reply(f":warning: {e.message}")
            except Exception as e:
                self.sentry_exc(e)
                error_message = f"🦀 [b]{e.__class__.__name__}[/b] 🦀\n" \
                                '\n'.join(e.args)
                await data.reply(error_message)
            finally:
                # Close the alchemy session
                if session is not None:
                    await asyncify(session.close)

    def _bot_factory(self) -> Type[discord.Client]:
        """Create a custom class inheriting from :py:class:`discord.Client`."""
        # noinspection PyMethodParameters
        class DiscordClient(discord.Client):
            async def on_message(cli, message: discord.Message):
                """Handle messages received by passing them to the handle_message method of the bot."""
                # TODO: keep reference to these tasks somewhere
                self.loop.create_task(self.handle_message(message))

            async def on_ready(cli) -> None:
                """Change the bot presence to ``online`` when the bot is ready."""
                await cli.change_presence(status=discord.Status.online)

            def find_guild(cli, name: str) -> List[discord.Guild]:
                """Find the :class:`discord.Guild`s with the specified name (case insensitive).

                Returns:
                    A :class:`list` of :class:`discord.Guild` having the specified name."""
                all_guilds: List[discord.Guild] = cli.guilds
                matching_channels: List[discord.Guild] = []
                for guild in all_guilds:
                    if guild.name.lower() == name.lower():
                        matching_channels.append(guild)
                return matching_channels

            def find_channel(cli,
                             name: str,
                             guild: Optional[discord.Guild] = None) -> List[discord.abc.GuildChannel]:
                """Find the :class:`TextChannel`, :class:`VoiceChannel` or :class:`CategoryChannel` with the
                specified name (case insensitive).

                You can specify a guild to only search in that specific guild."""
                if guild is not None:
                    all_channels = guild.channels
                else:
                    all_channels: List[discord.abc.GuildChannel] = cli.get_all_channels()
                matching_channels: List[discord.abc.GuildChannel] = []
                for channel in all_channels:
                    if not (isinstance(channel, discord.TextChannel)
                            or isinstance(channel, discord.VoiceChannel)
                            or isinstance(channel, discord.CategoryChannel)):
                        continue
                    if channel.name.lower() == name.lower():
                        matching_channels.append(channel)
                return matching_channels

            def find_voice_client(cli, guild: discord.Guild) -> Optional[discord.VoiceClient]:
                """Find the :py:class:`discord.VoiceClient` belonging to a specific :py:class:`discord.Guild`."""
                # TODO: the bug I was looking for might be here
                for voice_client in cli.voice_clients:
                    if voice_client.guild == guild:
                        return voice_client
                return None

        return DiscordClient

    # TODO: restart from here

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
        if guild_music_data is None:
            raise CommandError(f"No music_data has been created for guild {guild}")
        for dfile in dfiles:
            log.debug(f"Adding {dfile} to music_data")
            await asyncify(dfile.ready_up)
            guild_music_data.playmode.add(dfile)
        if guild_music_data.playmode.now_playing is None:
            await self.advance_music_data(guild)

    async def advance_music_data(self, guild: discord.Guild):
        """Try to play the next song, while it exists. Otherwise, just return."""
        guild_music_data: MusicData = self.music_data[guild]
        voice_client: discord.VoiceClient = guild_music_data.voice_client
        next_source: discord.AudioSource = await guild_music_data.playmode.next()
        await self.update_activity_with_source_title()
        if next_source is None:
            log.debug(f"Ending playback chain")
            return

        def advance(error=None):
            if error:
                voice_client.disconnect(force=True)
                guild_music_data.voice_client = None
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
