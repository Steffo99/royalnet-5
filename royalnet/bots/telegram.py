import telegram
import asyncio
import typing
import logging as _logging
import sys
from .generic import GenericBot
from ..commands import NullCommand
from ..utils import asyncify, Call, Command
from ..error import UnregisteredError, InvalidConfigError
from ..network import RoyalnetLink, Message, RequestError, RoyalnetConfig
from ..database import Alchemy, relationshiplinkchain, DatabaseConfig

loop = asyncio.get_event_loop()
log = _logging.getLogger(__name__)


async def todo(message: Message):
    log.warning(f"Skipped {message} because handling isn't supported yet.")


class TelegramConfig:
    def __init__(self, token: str):
        self.token: str = token


class TelegramBot(GenericBot):
    interface_name = "telegram"

    def _init_client(self):
        self.client = telegram.Bot(self._telegram_config.token)
        self._offset: int = -100

    def _call_factory(self) -> typing.Type[Call]:
        # noinspection PyMethodParameters
        class TelegramCall(Call):
            interface_name = self.interface_name
            interface_obj = self
            interface_prefix = "/"

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
                if self.network is None:
                    raise InvalidConfigError("Royalnet is not enabled on this bot")
                response: Message = await self.network.request(message, destination)
                response.raise_on_error()
                return response

            async def get_author(call, error_if_none=False):
                update: telegram.Update = call.kwargs["update"]
                user: telegram.User = update.effective_user
                if user is None:
                    if error_if_none:
                        raise UnregisteredError("No author for this message")
                    return None
                query = call.session.query(self.master_table)
                for link in self.identity_chain:
                    query = query.join(link.mapper.class_)
                query = query.filter(self.identity_column == user.id)
                result = await asyncify(query.one_or_none)
                if result is None and error_if_none:
                    raise UnregisteredError("Author is not registered")
        return TelegramCall

    def __init__(self, *,
                 telegram_config: TelegramConfig,
                 royalnet_config: typing.Optional[RoyalnetConfig] = None,
                 database_config: typing.Optional[DatabaseConfig] = None,
                 command_prefix: str = "/",
                 commands: typing.List[typing.Type[Command]] = None,
                 missing_command: typing.Type[Command] = NullCommand,
                 error_command: typing.Type[Command] = NullCommand):
        super().__init__(royalnet_config=royalnet_config,
                         database_config=database_config,
                         command_prefix=command_prefix,
                         commands=commands,
                         missing_command=missing_command,
                         error_command=error_command)
        self._telegram_config = telegram_config
        self._init_client()

    async def _handle_update(self, update: telegram.Update):
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
        command_name = command_text.replace(f"@{self.client.username}", "").lower()
        # Call the command
        await self.call(command_name, update.message.chat, parameters, update=update)

    async def run(self):
        while True:
            # Get the latest 100 updates
            try:
                last_updates: typing.List[telegram.Update] = await asyncify(self.client.get_updates, offset=self._offset, timeout=60)
            except telegram.error.TimedOut:
                continue
            # Handle updates
            for update in last_updates:
                # noinspection PyAsyncCall
                loop.create_task(self._handle_update(update))
            # Recalculate offset
            try:
                self._offset = last_updates[-1].update_id + 1
            except IndexError:
                pass

    @property
    def botfather_command_string(self) -> str:
        string = ""
        for command_key in self.commands:
            command = self.commands[command_key]
            string += f"{command.command_name} - {command.command_description}\n"
        return string
