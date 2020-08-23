import contextlib
import io
import logging
from typing import *

from royalnet.backpack.tables.users import User
from .errors import *

if TYPE_CHECKING:
    from .keyboardkey import KeyboardKey
    from .command import Command

log = logging.getLogger(__name__)


class CommandData:
    def __init__(self, command: "Command"):
        self.command: "Command" = command

    @property
    def loop(self):
        return self.command.loop

    @property
    def alchemy(self):
        """A shortcut for :attr:`.command.alchemy`."""
        return self.command.alchemy

    @property
    def session_acm(self):
        """A shortcut for :attr:`.alchemy.session_acm`."""
        return self.alchemy.session_acm

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

    async def delete_invoking(self, error_if_unavailable: bool = False) -> None:
        """Delete the invoking message, if supported by the interface.

        The invoking message is the message send by the user that contains the command.

        Parameters:
            error_if_unavailable: if True, raise an exception if the message cannot been deleted."""
        if error_if_unavailable:
            raise UnsupportedError(f"'{self.delete_invoking.__name__}' is not supported")

    async def find_author(self, *, session, required: bool = False) -> Optional["User"]:
        """Try to find the identifier of the user that sent the message.
        That probably means, the database row identifying the user.

        Parameters:
            session: the session that the user should be returned from.
            required: Raise an exception if this is True and the call has no author.
        """
        raise UnsupportedError(f"'{self.find_author.__name__}' is not supported")

    async def find_user(self, identifier: Union[str, int], *, session, required: bool = False) -> Optional["User"]:
        """Find the User having a specific identifier.

        Parameters:
            identifier: the identifier to search for.
            session: the session that the user should be returned from.
            required: Raise an exception if this is True and no user was found..
        """
        user: Optional["User"] = await User.find(alchemy=self.alchemy, session=session, identifier=identifier)
        if required and user is None:
            raise InvalidInputError(f"User '{identifier}' was not found.")
        return user

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
