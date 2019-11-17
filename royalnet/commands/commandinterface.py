from typing import Optional, TYPE_CHECKING, Awaitable, Any, Callable
from asyncio import AbstractEventLoop
from .errors import UnsupportedError
if TYPE_CHECKING:
    from .command import Command
    from ..alchemy import Alchemy
    from ..serf import Serf


class CommandInterface:
    name: str = NotImplemented
    """The name of the :class:`CommandInterface` that's being implemented.
    
    Examples:
        ``telegram``, ``discord``, ``console``..."""

    prefix: str = NotImplemented
    """The prefix used by commands on the interface.
    
    Examples:
        ``/`` on Telegram, ``!`` on Discord"""

    serf: "Serf" = NotImplemented
    """A reference to the Serf that is implementing this :class:`CommandInterface`.
    
    Examples:
        A reference to a :class:`~royalnet.serf.telegram.TelegramSerf`."""

    @property
    def alchemy(self):
        """A shortcut for :attr:`serf.alchemy`."""
        return self.serf.alchemy

    @property
    def loop(self):
        """A shortcut for :attr:`serf.loop`."""
        return self.serf.loop

    def __init__(self):
        self.command: Optional[Command] = None  # Will be bound after the command has been created

    def register_herald_action(self,
                               event_name: str,
                               coroutine: Callable[[Any], Awaitable[dict]]):
        # TODO: document this
        raise UnsupportedError(f"{self.register_herald_action.__name__} is not supported on this platform")

    def unregister_herald_action(self, event_name: str):
        # TODO: document this
        raise UnsupportedError(f"{self.unregister_herald_action.__name__} is not supported on this platform")

    async def call_herald_action(self, destination: str, event_name: str, args: dict) -> dict:
        # TODO: document this
        raise UnsupportedError(f"{self.call_herald_action.__name__} is not supported on this platform")
