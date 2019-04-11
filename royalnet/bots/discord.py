import discord
import asyncio
import typing
import logging as _logging
import sys
from ..commands import NullCommand
from ..utils import asyncify, Call, Command, UnregisteredError
from ..network import RoyalnetLink, Message
from ..database import Alchemy, relationshiplinkchain

loop = asyncio.get_event_loop()
log = _logging.getLogger(__name__)


async def todo(message: Message):
    log.warning(f"Skipped {message} because handling isn't supported yet.")


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
        self.missing_command = missing_command
        self.error_command = error_command
        self.network: RoyalnetLink = RoyalnetLink(master_server_uri, master_server_secret, "discord", todo)
        # Generate commands
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

    async def run(self):
        await self.bot.login(self.token)
        await self.bot.connect()
        # TODO: how to stop?
