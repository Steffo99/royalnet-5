import logging
import asyncio
import warnings
import uuid
from typing import Type, Optional, Dict, List, Tuple, Callable
import telegram
import urllib3
import sentry_sdk
from telegram.utils.request import Request as TRequest
from royalnet.commands import Command, CommandInterface, CommandData, CommandArgs, CommandError, InvalidInputError, \
                              UnsupportedError, KeyboardExpiredError
from royalnet.herald import Config as HeraldConfig
from royalnet.utils import asyncify
from .escape import escape
from ..alchemyconfig import AlchemyConfig
from ..serf import Serf

log = logging.getLogger(__name__)


class TelegramSerf(Serf):
    """A Serf that connects to `Telegram <https://telegram.org/>`_."""
    interface_name = "telegram"

    def __init__(self, *,
                 alchemy_config: Optional[AlchemyConfig] = None,
                 commands: List[Type[Command]] = None,
                 network_config: Optional[HeraldConfig] = None,
                 secrets_name: str = "__default__"):
        super().__init__(alchemy_config=alchemy_config,
                         commands=commands,
                         network_config=network_config,
                         secrets_name=secrets_name)

        self.client = telegram.Bot(self.get_secret("telegram"), request=TRequest(5, read_timeout=30))
        """The :class:`telegram.Bot` instance that will be used from the Serf."""

        self.update_offset: int = -100
        """The current `update offset <https://core.telegram.org/bots/api#getupdates>`_."""

    @staticmethod
    async def api_call(f: Callable, *args, **kwargs) -> Optional:
        """Call a :class:`telegram.Bot` method safely, without getting a mess of errors raised.

        The method may return None if it was decided that the call should be skipped."""
        while True:
            try:
                return await asyncify(f, *args, **kwargs)
            except telegram.error.TimedOut as error:
                log.debug(f"Timed out during {f.__qualname__} (retrying immediatly): {error}")
                continue
            except telegram.error.NetworkError as error:
                log.debug(f"Network error during {f.__qualname__} (skipping): {error}")
                break
            except telegram.error.Unauthorized as error:
                log.info(f"Unauthorized to run {f.__qualname__} (skipping): {error}")
                break
            except telegram.error.RetryAfter as error:
                log.warning(f"Rate limited during {f.__qualname__} (retrying in 15s): {error}")
                await asyncio.sleep(15)
                continue
            except urllib3.exceptions.HTTPError as error:
                log.warning(f"urllib3 HTTPError during {f.__qualname__} (retrying in 15s): {error}")
                await asyncio.sleep(15)
                continue
            except Exception as error:
                log.error(f"{error.__class__.__qualname__} during {f} (skipping): {error}")
                sentry_sdk.capture_exception(error)
                break
        return None

    def interface_factory(self) -> Type[CommandInterface]:
        # noinspection PyPep8Naming
        GenericInterface = super().interface_factory()

        # noinspection PyMethodParameters
        class TelegramInterface(GenericInterface):
            name = self.interface_name
            prefix = "/"

            def __init__(self):
                super().__init__()
                self.keys_callbacks: Dict[..., Callable] = {}

            def register_keyboard_key(interface, key_name: ..., callback: Callable):
                warnings.warn("register_keyboard_key is deprecated", category=DeprecationWarning)
                interface.keys_callbacks[key_name] = callback

            def unregister_keyboard_key(interface, key_name: ...):
                warnings.warn("unregister_keyboard_key is deprecated", category=DeprecationWarning)
                try:
                    del interface.keys_callbacks[key_name]
                except KeyError:
                    raise KeyError(f"Key '{key_name}' is not registered")

        return TelegramInterface

    def data_factory(self) -> Type[CommandData]:
        # noinspection PyMethodParameters
        class TelegramData(CommandData):
            def __init__(data, interface: CommandInterface, update: telegram.Update):
                super().__init__(interface)
                data.update = update

            async def reply(data, text: str):
                await self.api_call(data.update.effective_chat.send_message,
                                    escape(text),
                                    parse_mode="HTML",
                                    disable_web_page_preview=True)

            async def get_author(data, error_if_none=False):
                if data.update.message is not None:
                    user: telegram.User = data.update.message.from_user
                elif data.update.callback_query is not None:
                    user: telegram.User = data.update.callback_query.from_user
                else:
                    raise CommandError("Command caller can not be determined")
                if user is None:
                    if error_if_none:
                        raise CommandError("No command caller for this message")
                    return None
                query = data.session.query(self._master_table)
                for link in self._identity_chain:
                    query = query.join(link.mapper.class_)
                query = query.filter(self._identity_column == user.id)
                result = await asyncify(query.one_or_none)
                if result is None and error_if_none:
                    raise CommandError("Command caller is not registered")
                return result

            async def keyboard(data, text: str, keyboard: Dict[str, Callable]) -> None:
                warnings.warn("keyboard is deprecated, please avoid using it", category=DeprecationWarning)
                tg_keyboard = []
                for key in keyboard:
                    press_id = uuid.uuid4()
                    tg_keyboard.append([telegram.InlineKeyboardButton(key, callback_data=str(press_id))])
                    data._interface.register_keyboard_key(key_name=str(press_id), callback=keyboard[key])
                await self.api_call(data.update.effective_chat.send_message,
                                    escape(text),
                                    reply_markup=telegram.InlineKeyboardMarkup(tg_keyboard),
                                    parse_mode="HTML",
                                    disable_web_page_preview=True)

            async def delete_invoking(data, error_if_unavailable=False) -> None:
                message: telegram.Message = data.update.message
                await self.api_call(message.delete)

        return TelegramData

    async def _handle_update(self, update: telegram.Update):
        """What should be done when a :class:`telegram.Update` is received?"""
        # Skip non-message updates
        if update.message is not None:
            await self._handle_message(update)
        elif update.callback_query is not None:
            await self._handle_callback_query(update)

    async def _handle_message(self, update: telegram.Update):
        """What should be done when a :class:`telegram.Message` is received?"""
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
        await self.api_call(update.message.chat.send_action, telegram.ChatAction.TYPING)
        # Find the command
        try:
            command = self.commands[command_name]
        except KeyError:
            # Skip the message
            return
        # Prepare data
        data = self.Data(interface=command.interface, update=update)
        try:
            # Run the command
            await command.run(CommandArgs(parameters), data)
        except InvalidInputError as e:
            await data.reply(f"⚠️ {e.message}\n"
                             f"Syntax: [c]/{command.name} {command.syntax}[/c]")
        except UnsupportedError as e:
            await data.reply(f"⚠️ {e.message}")
        except CommandError as e:
            await data.reply(f"⚠️ {e.message}")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            error_message = f"🦀 [b]{e.__class__.__name__}[/b] 🦀\n"
            error_message += '\n'.join(e.args)
            await data.reply(error_message)
        finally:
            # Close the data session
            await data.session_close()

    async def _handle_callback_query(self, update: telegram.Update):
        query: telegram.CallbackQuery = update.callback_query
        source: telegram.Message = query.message
        callback: Optional[Callable] = None
        command: Optional[Command] = None
        for command in self.commands.values():
            if query.data in command.interface.keys_callbacks:
                callback = command.interface.keys_callbacks[query.data]
                break
        if callback is None:
            await self.api_call(source.edit_reply_markup, reply_markup=None)
            await self.api_call(query.answer, text="⛔️ This keyboard has expired.")
            return
        try:
            response = await callback(data=self.Data(interface=command.interface, update=update))
        except KeyboardExpiredError as e:
            # FIXME: May cause a memory leak, as keys are not deleted after use
            await self.safe_api_call(source.edit_reply_markup, reply_markup=None)
            if len(e.args) > 0:
                await self.safe_api_call(query.answer, text=f"⛔️ {e.args[0]}")
            else:
                await self.safe_api_call(query.answer, text="⛔️ This keyboard has expired.")
            return
        except Exception as e:
            error_text = f"⛔️ {e.__class__.__name__}\n"
            error_text += '\n'.join(e.args)
            await self.safe_api_call(query.answer, text=error_text)
        else:
            await self.safe_api_call(query.answer, text=response)

    def _initialize(self):
        super()._initialize()
        self._init_client()

    async def run(self):
        if not self.initialized:
            self._initialize()
        while True:
            # Get the latest 100 updates
            last_updates: List[telegram.Update] = await self.safe_api_call(self.client.get_updates,
                                                                           offset=self._offset,
                                                                           timeout=30,
                                                                           read_latency=5.0)
            # Handle updates
            for update in last_updates:
                # noinspection PyAsyncCall
                self.loop.create_task(self._handle_update(update))
            # Recalculate offset
            try:
                self._offset = last_updates[-1].update_id + 1
            except IndexError:
                pass
