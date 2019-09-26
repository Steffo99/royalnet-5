import typing


class CommandData:
    async def reply(self, text: str) -> None:
        """Send a text message to the channel where the call was made.

        Parameters:
             text: The text to be sent, possibly formatted in the weird undescribed markup that I'm using."""
        raise NotImplementedError()

    async def get_author(self, error_if_none: bool = False):
        """Try to find the identifier of the user that sent the message.
        That probably means, the database row identifying the user.

        Parameters:
            error_if_none: Raise a :py:exc:`royalnet.error.UnregisteredError` if this is True and the call has no author.

        Raises:
             :py:exc:`royalnet.error.UnregisteredError` if ``error_if_none`` is set to True and no author is found."""
        raise NotImplementedError()

    async def keyboard(self, text: str, keyboard: typing.Dict[str, typing.Callable]) -> None:
        """Send a keyboard having the keys of the dict as keys and calling the correspondent values on a press.

        The function should be passed the :py:class:`CommandData` instance as a argument."""
        raise NotImplementedError()

    async def delete_invoking(self, error_if_unavailable=False):
        """Delete the invoking message, if supported by the interface.

        The invoking message is the message send by the user that contains the command.

        Parameters:
            error_if_unavailable: if True, raise NotImplementedError() if the message cannot been deleted"""
        if error_if_unavailable:
            raise NotImplementedError()
