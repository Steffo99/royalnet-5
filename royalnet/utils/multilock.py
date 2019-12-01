from asyncio import Event
from contextlib import asynccontextmanager
import logging


log = logging.getLogger(__name__)


class MultiLock:
    """A lock that can allow both simultaneous access and exclusive access to a resource."""
    def __init__(self):
        self._counter: int = 0
        self._normal_event: Event = Event()
        self._exclusive_event: Event = Event()
        self._normal_event.set()
        self._exclusive_event.set()

    def _check_event(self):
        if self._counter > 0:
            self._normal_event.clear()
        else:
            self._normal_event.set()

    @asynccontextmanager
    async def normal(self):
        """Acquire the lock for simultaneous access."""
        log.debug(f"Waiting for exclusive lock end: {self}")
        await self._exclusive_event.wait()
        log.debug(f"Acquiring normal lock: {self}")
        self._counter += 1
        self._check_event()
        try:
            yield
        finally:
            log.debug(f"Releasing normal lock: {self}")
            self._counter -= 1
            self._check_event()

    @asynccontextmanager
    async def exclusive(self):
        """Acquire the lock for exclusive access."""
        log.debug(f"Waiting for exclusive lock end: {self}")
        # TODO: check if this actually works
        await self._exclusive_event.wait()
        self._exclusive_event.clear()
        log.debug(f"Waiting for normal lock end: {self}")
        await self._normal_event.wait()
        try:
            log.debug(f"Acquiring exclusive lock: {self}")
            self._exclusive_event.clear()
            yield
        finally:
            log.debug(f"Releasing exclusive lock: {self}")
            self._exclusive_event.set()

    def __repr__(self):
        return f"<MultiLock {self._counter} " \
               f"{'_' if self._normal_event.is_set() else 'N'}{'_' if self._exclusive_event.is_set() else 'E'}>"
