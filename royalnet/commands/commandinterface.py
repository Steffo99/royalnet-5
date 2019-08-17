import typing
if typing.TYPE_CHECKING:
    from ..database import Alchemy
    from ..bots import GenericBot


class CommandInterface:
    name: str = NotImplemented
    prefix: str = NotImplemented
    alchemy: "Alchemy" = NotImplemented
    bot: "GenericBot" = NotImplemented

    def __init__(self, alias: str):
        self.session = self.alchemy.Session()

    async def reply(self, text: str) -> None:
        """Send a text message to the channel where the call was made.

        Parameters:
             text: The text to be sent, possibly formatted in the weird undescribed markup that I'm using."""
        raise NotImplementedError()

    async def net_request(self, message, destination: str) -> dict:
        """Send data through a :py:class:`royalnet.network.RoyalnetLink` and wait for a :py:class:`royalnet.network.Reply`.

        Parameters:
            message: The data to be sent. Must be :py:mod:`pickle`-able.
            destination: The destination of the request, either in UUID format or node name."""
        raise NotImplementedError()

    async def get_author(self, error_if_none: bool = False):
        """Try to find the identifier of the user that sent the message.
        That probably means, the database row identifying the user.

        Parameters:
            error_if_none: Raise a :py:exc:`royalnet.error.UnregisteredError` if this is True and the call has no author.

        Raises:
             :py:exc:`royalnet.error.UnregisteredError` if ``error_if_none`` is set to True and no author is found."""
        raise NotImplementedError()

    def register_net_handler(self, message_type: str, network_handler: typing.Callable):
        """Register a new handler for messages received through Royalnet."""
        raise NotImplementedError()
