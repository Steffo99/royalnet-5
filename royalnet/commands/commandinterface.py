import typing
import asyncio
import royalherald as rh
from .commanderrors import UnsupportedError
if typing.TYPE_CHECKING:
    from .command import Command
    from ..database import Alchemy
    from ..bots import GenericBot


class CommandInterface:
    name: str = NotImplemented
    prefix: str = NotImplemented
    alchemy: "Alchemy" = NotImplemented
    bot: "GenericBot" = NotImplemented
    loop: asyncio.AbstractEventLoop = NotImplemented

    def __init__(self):
        self.command: typing.Optional[Command] = None  # Will be bound after the command has been created

    def register_herald_action(self,
                               event_name: str,
                               coroutine: typing.Callable[[typing.Any], typing.Awaitable[typing.Dict]]):
        raise UnsupportedError(f"{self.register_herald_action.__name__} is not supported on this platform")

    def unregister_herald_action(self, event_name: str):
        raise UnsupportedError(f"{self.unregister_herald_action.__name__} is not supported on this platform")

    async def call_herald_action(self, destination: str, event_name: str, args: typing.Dict) -> typing.Dict:
        raise UnsupportedError(f"{self.call_herald_action.__name__} is not supported on this platform")

    def register_keyboard_key(self, key_name: str, callback: typing.Callable):
        raise UnsupportedError(f"{self.register_keyboard_key.__name__} is not supported on this platform")

    def unregister_keyboard_key(self, key_name: str):
        raise UnsupportedError(f"{self.unregister_keyboard_key.__name__} is not supported on this platform")
