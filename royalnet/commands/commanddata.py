from typing import *
import contextlib
import logging
import asyncio as aio
import royalnet.utils as ru
import io
from .errors import UnsupportedError
from .commandinterface import CommandInterface
from royalnet.backpack.tables.aliases import Alias

if TYPE_CHECKING:
    from .keyboardkey import KeyboardKey
    from royalnet.backpack.tables.users import User

log = logging.getLogger(__name__)


class CommandData:
    def __init__(self, interface: CommandInterface, loop: aio.AbstractEventLoop):
        self.loop: aio.AbstractEventLoop = loop
        self._interface: CommandInterface = interface
        self._session = None

    # TODO: make this asyncronous... somehow?
    @property
    def session(self):
        if self._session is None:
            if self._interface.alchemy is None:
                raise UnsupportedError("'alchemy' is not enabled on this Royalnet instance")
            log.debug("Creating Session...")
            self._session = self._interface.alchemy.Session()
        return self._session

    async def session_commit(self):
        """Asyncronously commit the :attr:`.session` of this object."""
        if self._session:
            log.warning("Session had to be created to be committed")
        # noinspection PyUnresolvedReferences
        log.debug("Committing Session...")
        await ru.asyncify(self.session.commit)

    async def session_close(self):
        """Asyncronously close the :attr:`.session` of this object."""
        if self._session is not None:
            log.debug("Closing Session...")
            await ru.asyncify(self._session.close)

    async def reply(self, text: str) -> None:
        """Send a text message to the channel where the call was made.

        Parameters:
             text: The text to be sent, possibly formatted in the weird undescribed markup that I'm using."""
        raise UnsupportedError(f"'{self.reply.__name__}' is not supported")

    async def reply_image(self, image: io.IOBase, caption: Optional[str] = None) -> None:
        """Send an image (with optionally a caption) to the channel where the call was made.

        Parameters:
            image: The bytes of the image to send.
            caption: The caption to attach to the image."""
        raise UnsupportedError(f"'{self.reply_image.__name__}' is not supported")

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

    async def find_user(self, alias: str) -> Optional["User"]:
        """Find the User having a specific Alias.

        Parameters:
            alias: the Alias to search for."""
        return await Alias.find_user(self._interface.alchemy, self.session, alias)

    @contextlib.asynccontextmanager
    async def keyboard(self, text, keys: List["KeyboardKey"]):
        yield
        raise UnsupportedError(f"{self.keyboard.__name__} is not supported")

    @classmethod
    def register_keyboard_key(cls, identifier: str, key: "KeyboardKey"):
        raise UnsupportedError(f"{cls.register_keyboard_key.__name__} is not supported")

    @classmethod
    def unregister_keyboard_key(cls, identifier: str):
        raise UnsupportedError(f"{cls.unregister_keyboard_key.__name__} is not supported")
