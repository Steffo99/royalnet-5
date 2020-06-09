import asyncio as aio
import logging
import warnings
import io
import sys
from typing import *
import royalnet.backpack.tables as rbt
import royalnet.commands as rc
from royalnet.utils import asyncify, sentry_exc
from royalnet.serf import Serf
from .escape import escape
from .voiceplayer import VoicePlayer
import discord


log = logging.getLogger(__name__)


class DiscordSerf(Serf):
    """A :class:`Serf` that connects to `Discord <https://discordapp.com/>`_ as a bot."""
    interface_name = "discord"

    _identity_table = rbt.Discord
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

        self.client = self.Client(status=discord.Status.do_not_disturb)
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

            async def reply_image(data, image: io.IOBase, caption: Optional[str] = None) -> None:
                await data.message.channel.send(caption, file=discord.File(image, 'image'))

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
            async def on_message(cli, message: "discord.Message") -> None:
                """Handle messages received by passing them to the handle_message method of the bot."""
                # TODO: keep reference to these tasks somewhere
                self.loop.create_task(self.handle_message(message))

            async def on_ready(cli) -> None:
                """Change the bot presence to ``online`` when the bot is ready."""
                log.debug("Discord client is ready!")
                await cli.change_presence(status=discord.Status.online, activity=None)

            async def on_resume(cli) -> None:
                log.debug("Discord client resumed connection.")

            async def on_error(self, event_method, *args, **kwargs):
                exc_type, exc_obj, exc_tb = sys.exc_info()
                sentry_exc(exc_obj)

        return DiscordClient

    async def run(self):
        await super().run()
        await self.client.login(self.token)
        while True:
            try:
                await self.client.connect(reconnect=False)
            except discord.GatewayNotFound:
                log.error("Discord Gateway not found! Retrying in 60 seconds...")
                await aio.sleep(60)
            except discord.ConnectionClosed:
                log.error("Discord connection was closed! Retrying in 15 seconds...")
                await aio.sleep(60)

    def find_voice_players(self, guild: "discord.Guild") -> List[VoicePlayer]:
        candidate_players: List[VoicePlayer] = []
        for player in self.voice_players:
            player: VoicePlayer
            if not player.voice_client.is_connected():
                continue
            if guild is not None and guild != player.voice_client.guild:
                continue
            candidate_players.append(player)
        if guild:
            assert len(candidate_players) <= 1
        return candidate_players
