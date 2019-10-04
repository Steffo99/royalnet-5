import typing
import asyncio
from .commanderrors import UnsupportedError
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
        if self.alchemy:
            self.session = self.alchemy.Session()
        else:
            self.session = None

    def register_net_handler(self, message_type: str, network_handler: typing.Callable):
        """Register a new handler for messages received through Royalnet."""
        raise UnsupportedError("'register_net_handler' is not supported on this platform")

    def unregister_net_handler(self, message_type: str):
        """Remove a Royalnet handler."""
        raise UnsupportedError("'unregister_net_handler' is not supported on this platform")

    async def net_request(self, message, destination: str) -> dict:
        """Send data through a :py:class:`royalnet.network.NetworkLink` and wait for a
        :py:class:`royalnet.network.Reply`.

        Parameters:
            message: The data to be sent. Must be :py:mod:`pickle`-able.
            destination: The destination of the request, either in UUID format or node name."""
        raise UnsupportedError("'net_request' is not supported on this platform")

    def register_keyboard_key(self, key_name: str, callback: typing.Callable):
        raise UnsupportedError("'register_keyboard_key' is not supported on this platform")

    def unregister_keyboard_key(self, key_name: str):
        raise UnsupportedError("'unregister_keyboard_key' is not supported on this platform")
