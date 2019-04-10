import telegram
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


# noinspection PyUnusedLocal
async def todo(message: Message):
    pass


class TelegramBot:
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
        self.bot: telegram.Bot = telegram.Bot(api_key)
        self.should_run: bool = False
        self.offset: int = -100
        self.missing_command = missing_command
        self.error_command = error_command
        self.network: RoyalnetLink = RoyalnetLink(master_server_uri, master_server_secret, "telegram", todo)
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
        class TelegramCall(Call):
            interface_name = "telegram"
            interface_obj = self
            alchemy = self.alchemy

            async def reply(call, text: str):
                escaped_text = text.replace("<", "&lt;") \
                                   .replace(">", "&gt;") \
                                   .replace("[b]", "<b>") \
                                   .replace("[/b]", "</b>") \
                                   .replace("[i]", "<i>") \
                                   .replace("[/i]", "</i>") \
                                   .replace("[u]", "<b>") \
                                   .replace("[/u]", "</b>") \
                                   .replace("[c]", "<code>") \
                                   .replace("[/c]", "</code>")
                await asyncify(call.channel.send_message, escaped_text, parse_mode="HTML")

            async def net_request(call, message: Message, destination: str):
                response = await self.network.request(message, destination)
                return response

            async def get_author(call, error_if_none=False):
                update: telegram.Update = call.kwargs["update"]
                user: telegram.User = update.effective_user
                if user is None:
                    if error_if_none:
                        raise UnregisteredError("Author is not registered!")
                    return None
                query = call.session.query(self.master_table)
                for link in self.identity_chain:
                    query = query.join(link.mapper.class_)
                query = query.filter(self.identity_column == user.id)
                result = await asyncify(query.one_or_none)
                if result is None and error_if_none:
                    raise UnregisteredError("Author is not registered!")
                return result

        self.TelegramCall = TelegramCall

    async def run(self):
        self.should_run = True
        while self.should_run:
            # Get the latest 100 updates
            try:
                last_updates: typing.List[telegram.Update] = await asyncify(self.bot.get_updates, offset=self.offset, timeout=60)
            except telegram.error.TimedOut:
                continue
            # Handle updates
            for update in last_updates:
                # noinspection PyAsyncCall
                asyncio.create_task(self.handle_update(update))
            # Recalculate offset
            try:
                self.offset = last_updates[-1].update_id + 1
            except IndexError:
                pass

    async def handle_update(self, update: telegram.Update):
        # Skip non-message updates
        if update.message is None:
            return
        message: telegram.Message = update.message
        text: str = message.text
        # Try getting the caption instead
        if text is None:
            text: str = message.caption
        # No text or caption, ignore the message
        if text is None:
            return
        # Find and clean parameters
        command_text, *parameters = text.split(" ")
        command_text.replace(f"@{self.bot.username}", "")
        # Find the function
        try:
            command = self.commands[command_text]
        except KeyError:
            # Skip inexistent commands
            command = self.missing_command
        # Call the command
        try:
            return await self.TelegramCall(message.chat, command, parameters, log,
                                           update=update).run()
        except Exception as exc:
            try:
                return await self.TelegramCall(message.chat, self.error_command, parameters, log,
                                               update=update,
                                               exception_info=sys.exc_info(),
                                               previous_command=command).run()
            except Exception as exc2:
                log.error(f"Exception in error handler command: {exc2}")

    def generate_botfather_command_string(self):
        string = ""
        for command_key in self.commands:
            command = self.commands[command_key]
            string += f"{command.command_name} - {command.command_description}\n"
        return string

    async def handle_net_request(self, message: Message):
        pass