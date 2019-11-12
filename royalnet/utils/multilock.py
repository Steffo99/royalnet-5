from asyncio import Event
from contextlib import asynccontextmanager


class MultiLock:
    """A lock that can allow both simultaneous access and exclusive access to a resource."""
    def __init__(self):
        self._counter: int = 0
        self._normal_event: Event = Event()
        self._exclusive_event: Event = Event()
        self._exclusive_event.set()

    def _check_event(self):
        if self._counter > 0:
            self._normal_event.clear()
        else:
            self._normal_event.set()

    @asynccontextmanager
    async def normal(self):
        """Acquire the lock for simultaneous access."""
        await self._exclusive_event.wait()
        self._counter += 1
        self._check_event()
        try:
            yield
        finally:
            self._counter -= 1
            self._check_event()

    @asynccontextmanager
    async def exclusive(self):
        """Acquire the lock for exclusive access."""
        # TODO: check if this actually works
        await self._exclusive_event.wait()
        self._exclusive_event.clear()
        await self._normal_event.wait()
        try:
            yield
        finally:
            self._exclusive_event.set()
