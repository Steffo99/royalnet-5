import asyncio as aio
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from ..serf import Serf
    from ..constellation import Constellation


class HeraldEvent:
    """A remote procedure call triggered by a :mod:`royalnet.herald` request."""

    name = NotImplemented
    """The event_name that will trigger this event."""

    def __init__(self, parent: Union["Serf", "Constellation"], config):
        self.parent: Union["Serf", "Constellation"] = parent
        self.config = config

    @property
    def alchemy(self):
        """A shortcut for :attr:`.parent.alchemy`."""
        return self.parent.alchemy

    @property
    def loop(self) -> aio.AbstractEventLoop:
        """A shortcut for :attr:`.parent.loop`."""
        return self.parent.loop

    async def run(self, **kwargs):
        raise NotImplementedError()
