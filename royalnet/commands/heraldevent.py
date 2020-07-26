import asyncio as aio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..serf import Serf


class HeraldEvent:
    """A remote procedure call triggered by a :mod:`royalnet.herald` request."""

    name = NotImplemented
    """The event_name that will trigger this event."""

    def __init__(self, serf, config):
        self.serf = serf
        self.config = config

    @property
    def alchemy(self):
        """A shortcut for :attr:`.interface.alchemy`."""
        return self.serf.alchemy

    @property
    def loop(self) -> aio.AbstractEventLoop:
        """A shortcut for :attr:`.interface.loop`."""
        return self.serf.loop

    async def run(self, **kwargs):
        raise NotImplementedError()
