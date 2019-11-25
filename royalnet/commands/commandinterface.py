from typing import *
from asyncio import AbstractEventLoop
from .errors import UnsupportedError
if TYPE_CHECKING:
    from .event import Event
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
    def alchemy(self) -> "Alchemy":
        """A shortcut for :attr:`serf.alchemy`."""
        return self.serf.alchemy

    @property
    def loop(self) -> AbstractEventLoop:
        """A shortcut for :attr:`serf.loop`."""
        return self.serf.loop

    def __init__(self, cfg: Dict[str, Any]):
        self.cfg: Dict[str, Any] = cfg
        """The config section for the pack of the command."""

        # Will be bound after the command/event has been created
        self.command: Optional[Command] = None
        self.event: Optional[Event] = None

    async def call_herald_event(self, destination: str, event_name: str, **kwargs) -> dict:
        """Call an event function on a different :class:`Serf`.

        For example, you can run a function on a :class:`DiscordSerf` from a :class:`TelegramSerf`."""
        raise UnsupportedError(f"{self.call_herald_event.__name__} is not supported on this platform")
