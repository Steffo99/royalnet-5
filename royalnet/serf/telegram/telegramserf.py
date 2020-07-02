import contextlib
import logging
import asyncio as aio
import uuid
from typing import *
import royalnet.commands as rc
import royalnet.utils as ru
import royalnet.backpack.tables as rbt
from .escape import escape
from ..serf import Serf
import io
import telegram
import urllib3
from telegram.utils.request import Request as TRequest

try:
    from sqlalchemy.orm.session import Session
except ImportError:
    Session = None

log = logging.getLogger(__name__)


class TelegramSerf(Serf):
    """A Serf that connects to `Telegram <https://telegram.org/>`_ as a bot."""
    interface_name = "telegram"

    _identity_table = rbt.Telegram
    _identity_column = "tg_id"

    def __init__(self,
                 loop: aio.AbstractEventLoop,
                 alchemy_cfg: Dict[str, Any],
                 herald_cfg: Dict[str, Any],
                 sentry_cfg: Dict[str, Any],
                 packs_cfg: Dict[str, Any],
                 serf_cfg: Dict[str, Any],
                 **_):
        if telegram is None:
            raise ImportError("'telegram' extra is not installed")

        super().__init__(loop=loop,
                         alchemy_cfg=alchemy_cfg,
                         herald_cfg=herald_cfg,
                         sentry_cfg=sentry_cfg,
                         packs_cfg=packs_cfg,
                         serf_cfg=serf_cfg)

        self.client = telegram.Bot(serf_cfg["token"],
                                   request=TRequest(serf_cfg["pool_size"],
                                                    read_timeout=serf_cfg["read_timeout"]))
        """The :class:`telegram.Bot` instance that will be used from the Serf."""

        self.update_offset: int = -100
        """The current `update offset <https://core.telegram.org/bots/api#getupdates>`_."""

        self.key_callbacks: Dict[str, rc.KeyboardKey] = {}

        self.MessageData: Type[rc.CommandData] = self.message_data_factory()
        self.CallbackData: Type[rc.CommandData] = self.callback_data_factory()

    @staticmethod
    async def api_call(f: Callable, *args, **kwargs) -> Optional:
        """Call a :class:`telegram.Bot` method safely, without getting a mess of errors raised.

        The method may return None if it was decided that the call should be skipped."""
        while True:
            try:
                return await ru.asyncify(f, *args, **kwargs)
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
                await aio.sleep(15)
                continue
            except urllib3.exceptions.HTTPError as error:
                log.warning(f"urllib3 HTTPError during {f.__qualname__} (retrying in 15s): {error}")
                await aio.sleep(15)
                continue
            except Exception as error:
                log.error(f"{error.__class__.__qualname__} during {f} (skipping): {error}")
                ru.sentry_exc(error)
                break
        return None

    def interface_factory(self) -> Type[rc.CommandInterface]:
        # noinspection PyPep8Naming
        GenericInterface = super().interface_factory()

        # noinspection PyMethodParameters
        class TelegramInterface(GenericInterface):
            name = self.interface_name
            prefix = "/"

        return TelegramInterface

    def message_data_factory(self) -> Type[rc.CommandData]:
        # noinspection PyMethodParameters
        class TelegramMessageData(rc.CommandData):
            def __init__(data,
                         interface: rc.CommandInterface,
                         loop: aio.AbstractEventLoop,
                         message: telegram.Message):
                super().__init__(interface=interface, loop=loop)
                data.message: telegram.Message = message

            async def reply(data, text: str):
                await self.api_call(data.message.chat.send_message,
                                    escape(text),
                                    parse_mode="HTML",
                                    disable_web_page_preview=True)

            async def reply_image(data, image: io.IOBase, caption: Optional[str] = None) -> None:
                await self.api_call(data.message.chat.send_photo,
                                    photo=image,
                                    caption=escape(caption) if caption is not None else None,
                                    parse_mode="HTML",
                                    disable_web_page_preview=True)

            async def get_author(data, error_if_none=False):
                user: Optional[telegram.User] = data.message.from_user
                if user is None:
                    if error_if_none:
                        raise rc.CommandError("No command caller for this message")
                    return None
                query = data.session.query(self.master_table)
                for link in self.identity_chain:
                    query = query.join(link.mapper.class_)
                query = query.filter(self.identity_column == user.id)
                result = await ru.asyncify(query.one_or_none)
                if result is None and error_if_none:
                    raise rc.CommandError("Command caller is not registered")
                return result

            async def delete_invoking(data, error_if_unavailable=False) -> None:
                await self.api_call(data.message.delete)

            @contextlib.asynccontextmanager
            async def keyboard(data, text: str, keys: List[rc.KeyboardKey]):
                tg_rows = []
                key_uids = []
                for key in keys:
                    uid: str = str(uuid.uuid4())
                    key_uids.append(uid)
                    self.register_keyboard_key(uid, key)
                    tg_button: telegram.InlineKeyboardButton = telegram.InlineKeyboardButton(key.text,
                                                                                             callback_data=uid)
                    tg_row: List[telegram.InlineKeyboardButton] = [tg_button]
                    tg_rows.append(tg_row)
                tg_markup: telegram.InlineKeyboardMarkup = telegram.InlineKeyboardMarkup(tg_rows)
                message: telegram.Message = await self.api_call(data.message.chat.send_message,
                                                                escape(text),
                                                                parse_mode="HTML",
                                                                disable_web_page_preview=True,
                                                                reply_markup=tg_markup)
                yield message
                await self.api_call(message.edit_reply_markup, reply_markup=None)
                for uid in key_uids:
                    self.unregister_keyboard_key(uid)

        return TelegramMessageData

    def callback_data_factory(self) -> Type[rc.CommandData]:
        # noinspection PyMethodParameters
        class TelegramKeyboardData(rc.CommandData):
            def __init__(data,
                         interface: rc.CommandInterface,
                         loop: aio.AbstractEventLoop,
                         cbq: telegram.CallbackQuery):
                super().__init__(interface=interface, loop=loop)
                data.cbq: telegram.CallbackQuery = cbq

            async def reply(data, text: str):
                await self.api_call(data.cbq.answer,
                                    escape(text))

            async def get_author(data, error_if_none=False):
                user = data.cbq.from_user
                if user is None:
                    if error_if_none:
                        raise rc.CommandError("No command caller for this message")
                    return None
                query = data.session.query(self.master_table)
                for link in self.identity_chain:
                    query = query.join(link.mapper.class_)
                query = query.filter(self.identity_column == user.id)
                result = await ru.asyncify(query.one_or_none)
                if result is None and error_if_none:
                    raise rc.CommandError("Command caller is not registered")
                return result

        return TelegramKeyboardData

    async def answer_cbq(self, cbq, text, alert=False):
        await self.api_call(cbq.answer, text=text, show_alert=alert)

    async def handle_update(self, update: telegram.Update):
        """Delegate :class:`telegram.Update` handling to the correct message type submethod."""
        if update.message is not None:
            await self.handle_message(update.message)
        elif update.edited_message is not None:
            pass
        elif update.channel_post is not None:
            pass
        elif update.edited_channel_post is not None:
            pass
        elif update.inline_query is not None:
            pass
        elif update.chosen_inline_result is not None:
            pass
        elif update.callback_query is not None:
            await self.handle_callback_query(update.callback_query)
        elif update.shipping_query is not None:
            pass
        elif update.pre_checkout_query is not None:
            pass
        elif update.poll is not None:
            pass
        else:
            log.warning(f"Unknown update type: {update}")

    async def handle_message(self, message: telegram.Message):
        """What should be done when a :class:`telegram.Message` is received?"""
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
        # Find the command
        try:
            command = self.commands[command_name]
        except KeyError:
            # Skip the message
            return
        # Send a typing notification
        await self.api_call(message.chat.send_action, telegram.ChatAction.TYPING)
        # Prepare data
        data = self.MessageData(interface=command.interface, loop=self.loop, message=message)
        # Call the command
        await self.call(command, data, parameters)

    async def handle_callback_query(self, cbq: telegram.CallbackQuery):
        uid = cbq.data
        if uid not in self.key_callbacks:
            await self.api_call(cbq.answer, text="⚠️ This keyboard has expired.", show_alert=True)
            return
        key: rc.KeyboardKey = self.key_callbacks[uid]
        data: rc.CommandData = self.CallbackData(interface=key.interface, loop=self.loop, cbq=cbq)
        await self.press(key, data)

    def register_keyboard_key(self, identifier: str, key: rc.KeyboardKey):
        self.key_callbacks[identifier] = key

    def unregister_keyboard_key(self, identifier: str):
        del self.key_callbacks[identifier]

    async def run(self):
        await super().run()
        while True:
            # Get the latest 100 updates
            last_updates: List[telegram.Update] = await self.api_call(self.client.get_updates,
                                                                      offset=self.update_offset,
                                                                      timeout=60,
                                                                      read_latency=5.0)
            # Handle updates
            for update in last_updates:
                # TODO: don't lose the reference to the task
                # noinspection PyAsyncCall
                self.loop.create_task(self.handle_update(update))
            # Recalculate offset
            try:
                self.update_offset = last_updates[-1].update_id + 1
            except IndexError:
                pass
