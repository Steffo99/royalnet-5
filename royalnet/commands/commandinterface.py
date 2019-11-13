from typing import Optional, TYPE_CHECKING, Awaitable, Any, Callable
from asyncio import AbstractEventLoop
from .errors import UnsupportedError
if TYPE_CHECKING:
    from .command import Command
    from ..alchemy import Alchemy
    from ..serf import Serf


class CommandInterface:
    name: str = NotImplemented
    prefix: str = NotImplemented
    alchemy: "Alchemy" = NotImplemented
    bot: "Serf" = NotImplemented
    loop: AbstractEventLoop = NotImplemented

    def __init__(self):
        self.command: Optional[Command] = None  # Will be bound after the command has been created

    def register_herald_action(self,
                               event_name: str,
                               coroutine: Callable[[Any], Awaitable[dict]]):
        raise UnsupportedError(f"{self.register_herald_action.__name__} is not supported on this platform")

    def unregister_herald_action(self, event_name: str):
        raise UnsupportedError(f"{self.unregister_herald_action.__name__} is not supported on this platform")

    async def call_herald_action(self, destination: str, event_name: str, args: dict) -> dict:
        raise UnsupportedError(f"{self.call_herald_action.__name__} is not supported on this platform")
