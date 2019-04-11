import discord
import asyncio
import typing
import logging as _logging
from ..commands import NullCommand
from ..utils import asyncify, Call, Command, UnregisteredError
from ..network import RoyalnetLink, Message
from ..database import Alchemy, relationshiplinkchain

loop = asyncio.get_event_loop()
log = _logging.getLogger(__name__)


async def todo(message: Message):
    log.warning(f"Skipped {message} because handling isn't supported yet.")


class DiscordBot:
    # noinspection PyMethodParameters
    class DiscordClient(discord.Client):
        pass

    def __init__(self,
                 api_key: str,
                 master_server_uri: str,
                 master_server_secret: str,
                 commands: typing.List[typing.Type[Command]],
                 database_uri: str,
                 master_table,
                 identity_table,
                 identity_column_name: str,
                 missing_command: typing.Type[Command] = NullCommand,
                 error_command: typing.Type[Command] = NullCommand):
        self.bot = self.DiscordClient()
        self.network: RoyalnetLink = RoyalnetLink(master_server_uri, master_server_secret, "discord", todo)
        # Generate commands
        self.commands = {}
        required_tables = set()
        for command in commands:
            self.commands[f"/{command.command_name}"] = command
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

            async def get_author(self, error_if_none=False):
                raise NotImplementedError()

        self.DiscordCall = DiscordCall

    async def run(self):
        raise NotImplementedError()
