import telegram
import telegram.utils.request
import typing
import asyncio
import sentry_sdk
import logging as _logging
from .generic import GenericBot
from ..utils import *
from ..error import *
from ..network import *
from ..database import *
from ..commands import *


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

    def _interface_factory(self) -> typing.Type[CommandInterface]:
        # noinspection PyPep8Naming
        GenericInterface = super()._interface_factory()

        # noinspection PyMethodParameters,PyAbstractClass
        class TelegramInterface(GenericInterface):
            name = self.interface_name
            prefix = "/"

        return TelegramInterface

    def _data_factory(self) -> typing.Type[CommandData]:
        # noinspection PyMethodParameters,PyAbstractClass
        class TelegramData(CommandData):
            def __init__(data, interface: CommandInterface, update: telegram.Update):
                data._interface = interface
                data.update = update

            async def reply(data, text: str):
                await asyncify(data.update.effective_chat.send_message, telegram_escape(text),
                               parse_mode="HTML",
                               disable_web_page_preview=True)

            async def get_author(data, error_if_none=False):
                user: telegram.User = data.update.effective_user
                if user is None:
                    if error_if_none:
                        raise UnregisteredError("No author for this message")
                    return None
                query = data._interface.session.query(self.master_table)
                for link in self.identity_chain:
                    query = query.join(link.mapper.class_)
                query = query.filter(self.identity_column == user.id)
                result = await asyncify(query.one_or_none)
                if result is None and error_if_none:
                    raise UnregisteredError("Author is not registered")
                return result

        return TelegramData

    def __init__(self, *,
                 telegram_config: TelegramConfig,
                 royalnet_config: typing.Optional[RoyalnetConfig] = None,
                 database_config: typing.Optional[DatabaseConfig] = None,
                 sentry_dsn: typing.Optional[str] = None,
                 commands: typing.List[typing.Type[Command]] = None):
        super().__init__(royalnet_config=royalnet_config,
                         database_config=database_config,
                         sentry_dsn=sentry_dsn,
                         commands=commands)
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
        if not text.startswith("/"):
            return
        # Find and clean parameters
        command_text, *parameters = text.split(" ")
        command_name = command_text.replace(f"@{self.client.username}", "").lower()
        # Send a typing notification
        update.message.chat.send_action(telegram.ChatAction.TYPING)
        # Find the command
        try:
            command = self.commands[command_name]
        except KeyError:
            # Skip the message
            return
        # Prepare data
        data = self._Data(interface=command.interface, update=update)
        # Run the command
        try:
            await command.run(CommandArgs(parameters), data)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            error_message = f"⛔️ [b]{e.__class__.__name__}[/b]\n"
            error_message += '\n'.join(e.args)
            await data.reply(error_message)

    async def run(self):
        while True:
            # Get the latest 100 updates
            try:
                last_updates: typing.List[telegram.Update] = await asyncify(self.client.get_updates,
                                                                            offset=self._offset,
                                                                            timeout=30,
                                                                            read_latency=5.0)
            except telegram.error.TimedOut as error:
                log.debug("getUpdates timed out")
                continue
            except Exception as error:
                log.error(f"Error while getting updates: {error.__class__.__name__} {error.args}")
                sentry_sdk.capture_exception(error)
                await asyncio.sleep(5)
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
