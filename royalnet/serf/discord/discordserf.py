import asyncio as aio
import logging
import warnings
from typing import *
import royalnet.backpack as rb
import royalnet.commands as rc
from royalnet.utils import asyncify
from royalnet.serf import Serf
from .escape import escape
from .voiceplayer import VoicePlayer


try:
    import discord
except ImportError:
    discord = None

try:
    from sqlalchemy.orm.session import Session
except ImportError:
    Session = None

try:
    from royalnet.herald import Config as HeraldConfig
except ImportError:
    HeraldConfig = None

log = logging.getLogger(__name__)


class DiscordSerf(Serf):
    """A :class:`Serf` that connects to `Discord <https://discordapp.com/>`_ as a bot."""
    interface_name = "discord"

    _identity_table = rb.tables.Discord
    _identity_column = "discord_id"

    def __init__(self,
                 loop: aio.AbstractEventLoop,
                 alchemy_cfg: Dict[str, Any],
                 herald_cfg: Dict[str, Any],
                 sentry_cfg: Dict[str, Any],
                 packs_cfg: Dict[str, Any],
                 serf_cfg: Dict[str, Any],
                 **_):
        if discord is None:
            raise ImportError("'discord' extra is not installed")

        super().__init__(loop=loop,
                         alchemy_cfg=alchemy_cfg,
                         herald_cfg=herald_cfg,
                         sentry_cfg=sentry_cfg,
                         packs_cfg=packs_cfg,
                         serf_cfg=serf_cfg)

        self.token = serf_cfg["token"]
        """The Discord bot token."""

        self.Client = self.client_factory()
        """The custom :class:`discord.Client` class that will be instantiated later."""

        self.client = self.Client()
        """The custom :class:`discord.Client` instance."""

        self.voice_players: List[VoicePlayer] = []
        """A :class:`list` of the :class:`VoicePlayer` in use by this :class:`DiscordSerf`."""

        self.Data: Type[rc.CommandData] = self.data_factory()

    def interface_factory(self) -> Type[rc.CommandInterface]:
        # noinspection PyPep8Naming
        GenericInterface = super().interface_factory()

        # noinspection PyMethodParameters,PyAbstractClass
        class DiscordInterface(GenericInterface):
            name = self.interface_name
            prefix = "!"

        return DiscordInterface

    def data_factory(self) -> Type[rc.CommandData]:
        # noinspection PyMethodParameters,PyAbstractClass
        class DiscordData(rc.CommandData):
            def __init__(data,
                         interface: rc.CommandInterface,
                         loop: aio.AbstractEventLoop,
                         message: "discord.Message"):
                super().__init__(interface=interface, loop=loop)
                data.message = message

            async def reply(data, text: str):
                await data.message.channel.send(escape(text))

            async def get_author(data, error_if_none=False):
                user: "discord.Member" = data.message.author
                query = data.session.query(self.master_table)
                for link in self.identity_chain:
                    query = query.join(link.mapper.class_)
                query = query.filter(self.identity_column == user.id)
                result = await asyncify(query.one_or_none)
                if result is None and error_if_none:
                    raise rc.CommandError("You must be registered to use this command.")
                return result

            async def delete_invoking(data, error_if_unavailable=False):
                await data.message.delete()

        return DiscordData

    async def handle_message(self, message: "discord.Message"):
        """Handle a Discord message by calling a command if appropriate."""
        text = message.content
        # Skip non-text messages
        if not text:
            return
        # Skip non-command updates
        if not text.startswith("!"):
            return
        # Skip bot messages
        author: Union["discord.User"] = message.author
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
            data = self.Data(interface=command.interface, loop=self.loop, message=message)
            # Call the command
            await self.call(command, data, parameters)
            # Close the alchemy session
            if session is not None:
                await asyncify(session.close)

    def client_factory(self) -> Type["discord.Client"]:
        """Create a custom class inheriting from :py:class:`discord.Client`."""
        # noinspection PyMethodParameters
        class DiscordClient(discord.Client):
            async def on_message(cli, message: "discord.Message"):
                """Handle messages received by passing them to the handle_message method of the bot."""
                # TODO: keep reference to these tasks somewhere
                self.loop.create_task(self.handle_message(message))

            async def on_ready(cli) -> None:
                """Change the bot presence to ``online`` when the bot is ready."""
                await cli.change_presence(status=discord.Status.online)

        return DiscordClient

    async def run(self):
        await super().run()
        await self.client.login(self.token)
        await self.client.connect()

    def find_channel(self,
                     channel_type: Optional[Type["discord.abc.GuildChannel"]] = None,
                     name: Optional[str] = None,
                     guild: Optional["discord.Guild"] = None,
                     accessible_to: List["discord.User"] = None,
                     required_permissions: List[str] = None) -> Optional["discord.abc.GuildChannel"]:
        """Find the best channel matching all requests.

        In case multiple channels match all requests, return the one with the most members connected.

        Args:
            channel_type: Filter channels by type (select only :class:`discord.VoiceChannel`,
                          :class:`discord.TextChannel`, ...).
            name: Filter channels by name starting with ``name`` (using :meth:`str.startswith`).
                  Note that some channel types don't have names; this check will be skipped for them.
            guild: Filter channels by guild, keep only channels inside this one.
            accessible_to: Filter channels by permissions, keeping only channels where *all* these users have
                           the required permissions.
            required_permissions: Filter channels by permissions, keeping only channels where the users have *all* these
                                  :class:`discord.Permissions`.

        Returns:
            Either a :class:`~discord.abc.GuildChannel`, or :const:`None` if no channels were found."""
        warnings.warn("This function will be removed soon.", category=DeprecationWarning)
        if accessible_to is None:
            accessible_to = []
        if required_permissions is None:
            required_permissions = []
        channels: List[discord.abc.GuildChannel] = []
        for ch in self.client.get_all_channels():
            if channel_type is not None and not isinstance(ch, channel_type):
                continue

            if name is not None:
                try:
                    ch_name: str = ch.name
                    if not ch_name.startswith(name):
                        continue
                except AttributeError:
                    pass

            ch_guild: "discord.Guild" = ch.guild
            if guild is not None and guild != ch_guild:
                continue

            for user in accessible_to:
                member: "discord.Member" = ch.guild.get_member(user.id)
                if member is None:
                    continue
                permissions: "discord.Permissions" = ch.permissions_for(member)
                missing_perms = False
                for permission in required_permissions:
                    if not permissions.__getattribute__(permission):
                        missing_perms = True
                        break
                if missing_perms:
                    continue

            channels.append(ch)

        if len(channels) == 0:
            return None
        else:
            # Give priority to channels with the most people
            def people_count(c: "discord.VoiceChannel"):
                return len(c.members)

            channels.sort(key=people_count, reverse=True)

            return channels[0]

    def find_voice_player(self, guild: "discord.Guild") -> Optional[VoicePlayer]:
        for voice_player in self.voice_players:
            if not voice_player.voice_client.is_connected():
                continue
            if voice_player.voice_client.guild == guild:
                return voice_player
        else:
            return None
