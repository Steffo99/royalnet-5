import typing
from .commanderrors import UnsupportedError


class CommandData:
    async def reply(self, text: str) -> None:
        """Send a text message to the channel where the call was made.

        Parameters:
             text: The text to be sent, possibly formatted in the weird undescribed markup that I'm using."""
        raise UnsupportedError("'reply' is not supported on this platform")

    async def get_author(self, error_if_none: bool = False):
        """Try to find the identifier of the user that sent the message.
        That probably means, the database row identifying the user.

        Parameters:
            error_if_none: Raise an exception if this is True and the call has no author."""
        raise UnsupportedError("'get_author' is not supported on this platform")

    async def keyboard(self, text: str, keyboard: typing.Dict[str, typing.Callable]) -> None:
        """Send a keyboard having the keys of the dict as keys and calling the correspondent values on a press.

        The function should be passed the :py:class:`CommandData` instance as a argument."""
        raise UnsupportedError("'keyboard' is not supported on this platform")

    async def delete_invoking(self, error_if_unavailable=False) -> None:
        """Delete the invoking message, if supported by the interface.

        The invoking message is the message send by the user that contains the command.

        Parameters:
            error_if_unavailable: if True, raise an exception if the message cannot been deleted."""
        if error_if_unavailable:
            raise UnsupportedError("'delete_invoking' is not supported on this platform")
