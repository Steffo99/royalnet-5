import asyncio as aio
import io
import logging
import sys
from typing import *

import discord

import royalnet.backpack.tables as rbt
import royalnet.commands as rc
from royalnet.serf import Serf
from royalnet.utils import asyncify, sentry_exc
from .escape import escape

log = logging.getLogger(__name__)


class DiscordSerf(Serf):
    """A :class:`Serf` that connects to `Discord <https://discordapp.com/>`_ as a bot."""
    interface_name = "discord"
    prefix = "!"

    def __init__(self,
                 loop: aio.AbstractEventLoop,
                 alchemy_cfg: rc.ConfigDict,
                 herald_cfg: rc.ConfigDict,
                 sentry_cfg: rc.ConfigDict,
                 packs_cfg: rc.ConfigDict,
                 serf_cfg: rc.ConfigDict,
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

        self.Data: Type[rc.CommandData] = self.data_factory()

    def data_factory(self) -> Type[rc.CommandData]:
        # noinspection PyMethodParameters,PyAbstractClass
        class DiscordData(rc.CommandData):
            def __init__(data,
                         command: rc.Command,
                         message: "discord.Message"):
                super().__init__(command=command)
                data.message: "discord.Message" = message

            async def reply(data, text: str):
                await data.message.channel.send(escape(text))

            async def reply_image(data, image: io.IOBase, caption: Optional[str] = None) -> None:
                await data.message.channel.send(caption, file=discord.File(image, 'image'))

            async def find_author(data,
                                  *,
                                  session,
                                  required: bool = False) -> Optional[rbt.User]:
                user: Union["discord.User", "discord.Member"] = data.message.author
                DiscordT = data.alchemy.get(rbt.Discord)
                result = await asyncify(
                    session.query(DiscordT).filter(DiscordT.discord_id == user.id).one_or_none
                )
                if result is None and required:
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
            log.debug("Skipping message as it had no text")
            return
        # Skip non-command updates
        if not text.startswith(self.prefix):
            log.debug(f"Skipping message as it didn't start with {self.prefix}")
            return
        # Skip bot messages
        author: Union["discord.User", "discord.Member"] = message.author
        if author.bot:
            log.debug(f"Skipping message as it was from another bot")
            return
        # Find and clean parameters
        command_text, *parameters = text.split(" ")
        # Don't use a case-sensitive command name
        command_name = command_text.lstrip(self.prefix).lower()
        log.debug(f"Parsed '{command_name}' as command name")
        # Find the command
        try:
            command = self.commands[command_name]
        except KeyError:
            # Skip the message
            log.debug(f"Skipping message as I could not find the command {command_name}")
            return
        # Call the command
        log.debug(f"Sending typing notification")
        with message.channel.typing():
            # Prepare data
            # noinspection PyArgumentList
            data = self.Data(command=command, message=message)
            # Call the command
            log.debug(f"Calling {command}")
            await self.call(command, data, parameters)

    def client_factory(self) -> Type["discord.Client"]:
        """Create a custom class inheriting from :py:class:`discord.Client`."""

        # noinspection PyMethodParameters
        class DiscordClient(discord.Client):
            # noinspection PyMethodMayBeStatic
            async def on_message(cli, message: "discord.Message") -> None:
                """Handle messages received by passing them to the handle_message method of the bot."""
                self.tasks.add(self.handle_message(message))

            async def on_ready(cli) -> None:
                """Change the bot presence to ``online`` when the bot is ready."""
                log.debug("Discord client is ready!")
                await cli.change_presence(status=discord.Status.online, activity=None)

            # noinspection PyMethodMayBeStatic
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
