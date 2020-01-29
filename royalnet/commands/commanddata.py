import contextlib
import logging
import asyncio as aio
from typing import *
from sqlalchemy.orm.session import Session
from .errors import UnsupportedError
from .commandinterface import CommandInterface
import royalnet.utils as ru
if TYPE_CHECKING:
    from .keyboardkey import KeyboardKey

log = logging.getLogger(__name__)


class CommandData:
    def __init__(self, interface: CommandInterface, loop: aio.AbstractEventLoop):
        self._interface: CommandInterface = interface
        self.loop: aio.AbstractEventLoop = loop
        self._session = None

    @property
    def session(self):
        if self._session is None:
            if self._interface.alchemy is None:
                raise UnsupportedError("'alchemy' is not enabled on this Royalnet instance")
            # FIXME: this may take a while
            self._session = self._interface.alchemy.Session()
        return self._session

    async def session_commit(self):
        if self._session:
            log.warning("Session had to be created to be committed")
        # noinspection PyUnresolvedReferences
        await ru.asyncify(self.session.commit)

    async def session_close(self):
        if self._session is not None:
            await ru.asyncify(self._session.close)

    async def reply(self, text: str) -> None:
        """Send a text message to the channel where the call was made.

        Parameters:
             text: The text to be sent, possibly formatted in the weird undescribed markup that I'm using."""
        raise UnsupportedError(f"'{self.reply.__name__}' is not supported")

    async def get_author(self, error_if_none: bool = False):
        """Try to find the identifier of the user that sent the message.
        That probably means, the database row identifying the user.

        Parameters:
            error_if_none: Raise an exception if this is True and the call has no author."""
        raise UnsupportedError(f"'{self.get_author.__name__}' is not supported")

    async def delete_invoking(self, error_if_unavailable=False) -> None:
        """Delete the invoking message, if supported by the interface.

        The invoking message is the message send by the user that contains the command.

        Parameters:
            error_if_unavailable: if True, raise an exception if the message cannot been deleted."""
        if error_if_unavailable:
            raise UnsupportedError(f"'{self.delete_invoking.__name__}' is not supported")

    @contextlib.asynccontextmanager
    async def keyboard(self, text, keys: List["KeyboardKey"]):
        yield
        raise UnsupportedError(f"{self.keyboard.__name__} is not supported")
