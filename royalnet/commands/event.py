from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from serf import Serf


class Event:
    """A remote procedure call triggered by a :mod:`royalnet.herald` request."""

    name = NotImplemented
    """The event_name that will trigger this event."""

    tables: set = set()
    """A set of :mod:`royalnet.alchemy` tables that must exist for this event to work."""

    def __init__(self, serf: Serf):
        """Bind the event to a :class:`~royalnet.serf.Serf`."""
        self.serf: Serf = serf

    @property
    def alchemy(self):
        """A shortcut for :attr:`.serf.alchemy`."""
        return self.serf.alchemy

    @property
    def loop(self):
        """A shortcut for :attr:`.serf.loop`"""
        return self.serf.loop

    async def run(self, data: dict):
        raise NotImplementedError()
