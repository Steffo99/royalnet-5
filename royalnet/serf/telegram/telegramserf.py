import logging
import asyncio as aio
from typing import *
from royalnet.commands import *
from royalnet.utils import asyncify
import royalnet.backpack as rb
from .escape import escape
from ..serf import Serf

try:
    import telegram
    import urllib3
    from telegram.utils.request import Request as TRequest
except ImportError:
    telegram = None
    urllib3 = None
    TRequest = None

try:
    from sqlalchemy.orm.session import Session
except ImportError:
    Session = None

log = logging.getLogger(__name__)


class TelegramSerf(Serf):
    """A Serf that connects to `Telegram <https://telegram.org/>`_ as a bot."""
    interface_name = "telegram"

    _identity_table = rb.tables.Telegram
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
                await aio.sleep(15)
                continue
            except urllib3.exceptions.HTTPError as error:
                log.warning(f"urllib3 HTTPError during {f.__qualname__} (retrying in 15s): {error}")
                await aio.sleep(15)
                continue
            except Exception as error:
                log.error(f"{error.__class__.__qualname__} during {f} (skipping): {error}")
                TelegramSerf.sentry_exc(error)
                break
        return None

    def interface_factory(self) -> Type[CommandInterface]:
        # noinspection PyPep8Naming
        GenericInterface = super().interface_factory()

        # noinspection PyMethodParameters
        class TelegramInterface(GenericInterface):
            name = self.interface_name
            prefix = "/"

        return TelegramInterface

    def data_factory(self) -> Type[CommandData]:
        # noinspection PyMethodParameters
        class TelegramData(CommandData):
            def __init__(data,
                         interface: CommandInterface,
                         session,
                         loop: aio.AbstractEventLoop,
                         update: telegram.Update):
                super().__init__(interface=interface, session=session, loop=loop)
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
                query = data.session.query(self.master_table)
                for link in self.identity_chain:
                    query = query.join(link.mapper.class_)
                query = query.filter(self.identity_column == user.id)
                result = await asyncify(query.one_or_none)
                if result is None and error_if_none:
                    raise CommandError("Command caller is not registered")
                return result

            async def delete_invoking(data, error_if_unavailable=False) -> None:
                message: telegram.Message = data.update.message
                await self.api_call(message.delete)

        return TelegramData

    async def handle_update(self, update: telegram.Update):
        """Delegate :class:`telegram.Update` handling to the correct message type submethod."""

        if update.message is not None:
            await self.handle_message(update)
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
            pass
        elif update.shipping_query is not None:
            pass
        elif update.pre_checkout_query is not None:
            pass
        elif update.poll is not None:
            pass
        else:
            log.warning(f"Unknown update type: {update}")

    async def handle_message(self, update: telegram.Update):
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
        # Find the command
        try:
            command = self.commands[command_name]
        except KeyError:
            # Skip the message
            return
        # Send a typing notification
        await self.api_call(update.message.chat.send_action, telegram.ChatAction.TYPING)
        # Prepare data
        if self.alchemy is not None:
            session = await asyncify(self.alchemy.Session)
        else:
            session = None
        # Prepare data
        data = self.Data(interface=command.interface, session=session, loop=self.loop, update=update)
        # Call the command
        await self.call(command, data, parameters)
        # Close the alchemy session
        if session is not None:
            await asyncify(session.close)

    async def handle_edited_message(self, update: telegram.Update):
        pass

    async def handle_channel_post(self, update: telegram.Update):
        pass

    async def handle_edited_channel_post(self, update: telegram.Update):
        pass

    async def handle_inline_query(self, update: telegram.Update):
        pass

    async def handle_chosen_inline_result(self, update: telegram.Update):
        pass

    async def handle_callback_query(self, update: telegram.Update):
        pass

    async def handle_shipping_query(self, update: telegram.Update):
        pass

    async def handle_pre_checkout_query(self, update: telegram.Update):
        pass

    async def handle_poll(self, update: telegram.Update):
        pass

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
