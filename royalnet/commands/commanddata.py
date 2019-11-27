from asyncio import AbstractEventLoop
from typing import Optional, TYPE_CHECKING
from .errors import UnsupportedError
from .commandinterface import CommandInterface
from ..utils import asyncify
from sqlalchemy.orm.session import Session


class CommandData:
    def __init__(self, interface: CommandInterface, session: Optional[Session], loop: AbstractEventLoop):
        self._interface: CommandInterface = interface
        self._session: Optional[Session] = session
        self.loop: AbstractEventLoop = loop

    @property
    def session(self) -> Session:
        """Get the :class:`~royalnet.alchemy.Alchemy` :class:`Session`, if it is available.

        Raises:
            UnsupportedError: if no session is available."""
        if self._session is None:
            raise UnsupportedError("'session' is not supported")
        return self._session

    async def session_commit(self):
        """Commit the changes to the session."""
        await asyncify(self.session.commit)

    async def reply(self, text: str) -> None:
        """Send a text message to the channel where the call was made.

        Parameters:
             text: The text to be sent, possibly formatted in the weird undescribed markup that I'm using."""
        raise UnsupportedError("'reply' is not supported")

    async def get_author(self, error_if_none: bool = False):
        """Try to find the identifier of the user that sent the message.
        That probably means, the database row identifying the user.

        Parameters:
            error_if_none: Raise an exception if this is True and the call has no author."""
        raise UnsupportedError("'get_author' is not supported")

    async def delete_invoking(self, error_if_unavailable=False) -> None:
        """Delete the invoking message, if supported by the interface.

        The invoking message is the message send by the user that contains the command.

        Parameters:
            error_if_unavailable: if True, raise an exception if the message cannot been deleted."""
        if error_if_unavailable:
            raise UnsupportedError("'delete_invoking' is not supported")
