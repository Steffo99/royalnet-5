import asyncio
import logging
from typing import Type, Optional, List, Union
from royalnet.commands import *
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

        self.Client = self.client_factory()
        """The custom :class:`discord.Client` class that will be instantiated later."""

        self.client = self.Client()
        """The custo :class:`discord.Client` instance."""

    def interface_factory(self) -> Type[CommandInterface]:
        # noinspection PyPep8Naming
        GenericInterface = super().interface_factory()

        # noinspection PyMethodParameters,PyAbstractClass
        class DiscordInterface(GenericInterface):
            name = self.interface_name
            prefix = "!"

        return DiscordInterface

    def data_factory(self) -> Type[CommandData]:
        # noinspection PyMethodParameters,PyAbstractClass
        class DiscordData(CommandData):
            def __init__(data,
                         interface: CommandInterface,
                         session,
                         loop: asyncio.AbstractEventLoop,
                         message: "discord.Message"):
                super().__init__(interface=interface, session=session, loop=loop)
                data.message = message

            async def reply(data, text: str):
                await data.message.channel.send(escape(text))

            async def get_author(data, error_if_none=False):
                user: "discord.Member" = data.message.author
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
            data = self.Data(interface=command.interface, session=session, loop=self.loop, message=message)
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

    def get_voice_client(self, guild: "discord.Guild") -> Optional["discord.VoiceClient"]:
        voice_clients: List["discord.VoiceClient"] = self.client.voice_clients
        for voice_client in voice_clients:
            if voice_client.guild == guild:
                return voice_client
        return None

    async def run(self):
        await super().run()
        token = self.get_secret("discord")
        await self.client.login(token)
        await self.client.connect()
