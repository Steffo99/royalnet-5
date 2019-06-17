import telegram
import telegram.utils.request
import asyncio
import typing
import logging as _logging
from .generic import GenericBot
from ..commands import NullCommand
from ..utils import asyncify, Call, Command, telegram_escape
from ..error import UnregisteredError, InvalidConfigError, RoyalnetResponseError
from ..network import RoyalnetConfig, Request, ResponseSuccess, ResponseError
from ..database import DatabaseConfig


log = _logging.getLogger(__name__)


class TelegramConfig:
    """The specific configuration to be used for :py:class:`royalnet.database.TelegramBot`."""
    def __init__(self, token: str):
        self.token: str = token


class TelegramBot(GenericBot):
    """A bot that connects to `Telegram <https://telegram.org/>`_."""
    interface_name = "telegram"

    def _init_client(self):
        """Create the :py:class:`telegram.Bot`, and set the starting offset."""
        # https://github.com/python-telegram-bot/python-telegram-bot/issues/341
        request = telegram.utils.request.Request(5)
        self.client = telegram.Bot(self._telegram_config.token, request=request)
        self._offset: int = -100

    def _call_factory(self) -> typing.Type[Call]:
        # noinspection PyMethodParameters
        class TelegramCall(Call):
            interface_name = self.interface_name
            interface_obj = self
            interface_prefix = "/"

            alchemy = self.alchemy

            async def reply(call, text: str):
                await asyncify(call.channel.send_message, telegram_escape(text), parse_mode="HTML")

            async def net_request(call, request: Request, destination: str) -> dict:
                if self.network is None:
                    raise InvalidConfigError("Royalnet is not enabled on this bot")
                response_dict: dict = await self.network.request(request.to_dict(), destination)
                if "type" not in response_dict:
                    raise RoyalnetResponseError("Response is missing a type")
                elif response_dict["type"] == "ResponseSuccess":
                    response: typing.Union[ResponseSuccess, ResponseError] = ResponseSuccess.from_dict(response_dict)
                elif response_dict["type"] == "ResponseError":
                    response = ResponseError.from_dict(response_dict)
                else:
                    raise RoyalnetResponseError("Response type is unknown")
                response.raise_on_error()
                return response.data

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
                return result

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
        # Skip non-command updates
        if not text.startswith(self.command_prefix):
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
                self.loop.create_task(self._handle_update(update))
            # Recalculate offset
            try:
                self._offset = last_updates[-1].update_id + 1
            except IndexError:
                pass

    @property
    def botfather_command_string(self) -> str:
        """Generate a string to be pasted in the "Edit Commands" BotFather prompt."""
        string = ""
        for command_key in self.commands:
            command = self.commands[command_key]
            string += f"{command.command_name} - {command.command_description}\n"
        return string
