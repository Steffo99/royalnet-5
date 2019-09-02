import typing
import asyncio
if typing.TYPE_CHECKING:
    from ..database import Alchemy
    from ..bots import GenericBot


class CommandInterface:
    name: str = NotImplemented
    prefix: str = NotImplemented
    alchemy: "Alchemy" = NotImplemented
    bot: "GenericBot" = NotImplemented
    loop: asyncio.AbstractEventLoop = NotImplemented

    def __init__(self):
        self.session = self.alchemy.Session()

    def register_net_handler(self, message_type: str, network_handler: typing.Callable):
        """Register a new handler for messages received through Royalnet."""
        raise NotImplementedError()

    def unregister_net_handler(self, message_type: str):
        """Remove a Royalnet handler."""
        raise NotImplementedError()

    async def net_request(self, message, destination: str) -> dict:
        """Send data through a :py:class:`royalnet.network.RoyalnetLink` and wait for a
        :py:class:`royalnet.network.Reply`.

        Parameters:
            message: The data to be sent. Must be :py:mod:`pickle`-able.
            destination: The destination of the request, either in UUID format or node name."""
        raise NotImplementedError()

    def register_keyboard_key(self, key_name: str, callback: typing.Callable):
        raise NotImplementedError()

    def unregister_keyboard_key(self, key_name: str):
        raise NotImplementedError()
