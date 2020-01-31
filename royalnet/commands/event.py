import asyncio as aio
from .commandinterface import CommandInterface
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from serf import Serf


class Event:
    """A remote procedure call triggered by a :mod:`royalnet.herald` request."""

    name = NotImplemented
    """The event_name that will trigger this event."""

    def __init__(self, interface: CommandInterface):
        """Bind the event to a :class:`~royalnet.serf.Serf`."""
        self.interface: CommandInterface = interface
        """The :class:`CommandInterface` available to this :class:`Event`."""

    @property
    def serf(self) -> "Serf":
        """A shortcut for :attr:`.interface.serf`."""
        return self.interface.serf

    @property
    def alchemy(self):
        """A shortcut for :attr:`.interface.alchemy`."""
        return self.interface.alchemy

    @property
    def loop(self) -> aio.AbstractEventLoop:
        """A shortcut for :attr:`.interface.loop`."""
        return self.interface.loop

    @property
    def config(self) -> dict:
        """A shortcut for :attr:`.interface.config`."""
        return self.interface.config

    async def run(self, **kwargs):
        raise NotImplementedError()
