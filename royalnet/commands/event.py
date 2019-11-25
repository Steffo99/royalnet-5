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
    def alchemy(self):
        """A shortcut for :attr:`.serf.alchemy`."""
        return self.interface.serf.alchemy

    @property
    def loop(self):
        """A shortcut for :attr:`.serf.loop`"""
        return self.interface.serf.loop

    async def run(self, **kwargs):
        raise NotImplementedError()
