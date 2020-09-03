import asyncio as aio
import contextlib
import logging
import uuid
from dataclasses import dataclass
from typing import *

import telegram
import urllib3
from telegram.utils.request import Request as TRequest

import royalnet.backpack.tables as rbt
import royalnet.commands as rc
import royalnet.utils as ru
from .escape import escape
from ..serf import Serf

try:
    from sqlalchemy.orm.session import Session
except ImportError:
    Session = None

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class TelegramKeyCallback:
    command: rc.Command
    key: rc.KeyboardKey


class TelegramSerf(Serf):
    """A Serf that connects to `Telegram <https://telegram.org/>`_ as a bot."""
    interface_name = "telegram"
    prefix = "/"

    def __init__(self,
                 loop: aio.AbstractEventLoop,
                 alchemy_cfg: rc.ConfigDict,
                 herald_cfg: rc.ConfigDict,
                 sentry_cfg: rc.ConfigDict,
                 packs_cfg: rc.ConfigDict,
                 serf_cfg: rc.ConfigDict,
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

        self.key_callbacks: Dict[str, TelegramKeyCallback] = {}

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

    def message_data_factory(self) -> Type[rc.CommandData]:
        # noinspection PyMethodParameters
        class TelegramMessageData(rc.CommandData):
            def __init__(data,
                         command: rc.Command,
                         message: telegram.Message):
                super().__init__(command=command)
                data.message: telegram.Message = message

            async def reply(data, text: str):
                await self.api_call(data.message.chat.send_message,
                                    escape(text),
                                    parse_mode="HTML",
                                    disable_web_page_preview=True)

            async def reply_image(data, image: "BinaryIO", caption: Optional[str] = None) -> None:
                await self.api_call(data.message.chat.send_photo,
                                    photo=image,
                                    caption=escape(caption) if caption is not None else None,
                                    parse_mode="HTML",
                                    disable_web_page_preview=True)

            async def find_author(data,
                                  *,
                                  session,
                                  required: bool = False) -> Optional[rbt.User]:
                user: "telegram.User" = data.message.from_user
                TelegramT = data.alchemy.get(rbt.Telegram)
                result = await ru.asyncify(
                    session.query(TelegramT).filter(TelegramT.tg_id == user.id).one_or_none
                )
                if result is None and required:
                    raise rc.CommandError("You must be registered to use this command.")
                return result.user

            async def delete_invoking(data, error_if_unavailable=False) -> None:
                await self.api_call(data.message.delete)

            @contextlib.asynccontextmanager
            async def keyboard(data, text: str, keys: List[rc.KeyboardKey]):
                tg_rows = []
                key_uids = []
                for key in keys:
                    uid: str = str(uuid.uuid4())
                    key_uids.append(uid)
                    data.register_keyboard_key(uid, key)
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
                    data.unregister_keyboard_key(uid)

            def register_keyboard_key(data, identifier: str, key: rc.KeyboardKey):
                self.key_callbacks[identifier] = TelegramKeyCallback(key=key, command=data.command)

            def unregister_keyboard_key(data, identifier: str):
                del self.key_callbacks[identifier]

        return TelegramMessageData

    def register_keyboard_key(self, identifier: str, key: rc.KeyboardKey, command: rc.Command):
        self.key_callbacks[identifier] = TelegramKeyCallback(key=key, command=command)

    def unregister_keyboard_key(self, identifier: str):
        del self.key_callbacks[identifier]

    def callback_data_factory(self) -> Type[rc.CommandData]:
        # noinspection PyMethodParameters
        class TelegramKeyboardData(rc.CommandData):
            def __init__(data,
                         command: rc.Command,
                         cbq: telegram.CallbackQuery):
                super().__init__(command=command)
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
                async with data.session_acm() as session:
                    query = session.query(self.master_table)
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
            log.debug(f"Handling update as a message")
            await self.handle_message(update.message)
        elif update.edited_message is not None:
            log.debug(f"Update is a edited message, not doing anything")
        elif update.channel_post is not None:
            log.debug(f"Update is a channel post, not doing anything")
        elif update.edited_channel_post is not None:
            log.debug(f"Update is a channel edit, not doing anything")
        elif update.inline_query is not None:
            log.debug(f"Update is a inline query, not doing anything")
        elif update.chosen_inline_result is not None:
            log.debug(f"Update is a chosen inline result, not doing anything")
        elif update.callback_query is not None:
            log.debug(f"Handling update as a callback query")
            await self.handle_callback_query(update.callback_query)
        elif update.shipping_query is not None:
            log.debug(f"Update is a shipping query, not doing anything")
        elif update.pre_checkout_query is not None:
            log.debug(f"Update is a precheckout query, not doing anything")
        elif update.poll is not None:
            log.debug(f"Update is a poll, not doing anything")
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
            log.debug("Skipping message as it had no text or caption")
            return
        # Skip non-command updates
        if not text.startswith(self.prefix):
            log.debug(f"Skipping message as it didn't start with {self.prefix}")
            return
        # Find and clean parameters
        command_text, *parameters = text.split(" ")
        command_name = command_text.replace(f"@{self.client.username}", "").lstrip(self.prefix).lower()
        log.debug(f"Parsed '{command_name}' as command name")
        # Find the command
        try:
            command = self.commands[command_name]
        except KeyError:
            # Skip the message
            log.debug(f"Skipping message as I could not find the command {command_name}")
            return
        # Send a typing notification
        log.debug(f"Sending typing notification")
        await self.api_call(message.chat.send_action, telegram.ChatAction.TYPING)
        # Prepare data
        # noinspection PyArgumentList
        data = self.MessageData(command=command, message=message)
        # Call the command
        log.debug(f"Calling {command}")
        await self.call(command, data, parameters)

    async def handle_callback_query(self, cbq: telegram.CallbackQuery):
        uid = cbq.data
        if uid not in self.key_callbacks:
            await self.api_call(cbq.answer, text="⚠️ This keyboard has expired.", show_alert=True)
            return
        cbd = self.key_callbacks[uid]
        # noinspection PyArgumentList
        data: rc.CommandData = self.CallbackData(command=cbd.command, cbq=cbq)
        await self.press(cbd.key, data)

    async def run(self):
        await super().run()
        while True:
            # Collect ended tasks
            self.tasks.collect()
            # Get the latest 100 updates
            log.debug("Getting updates...")
            last_updates: Optional[List[telegram.Update]] = await self.api_call(
                self.client.get_updates,
                offset=self.update_offset,
                timeout=60,
                read_latency=5.0
            )
            # Ensure a list was returned from the API call
            if not isinstance(last_updates, list):
                log.warning("Received invalid data from get_updates, sleeping for 60 seconds, hoping it fixes itself.")
                await aio.sleep(60)
                continue
            # Handle updates
            log.debug("Handling updates...")
            for update in last_updates:
                self.tasks.add(self.handle_update(update))
            # Recalculate offset
            try:
                self.update_offset = last_updates[-1].update_id + 1
            except IndexError:
                pass
