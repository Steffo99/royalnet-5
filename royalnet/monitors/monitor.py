import asyncio
import time


class Monitor:
    def __init__(self, interval: float, *, loop: asyncio.AbstractEventLoop):
        self.interval: float = interval
        self._loop: asyncio.AbstractEventLoop = loop
        self.last_check_start: float = 0.0
        self.last_check_end: float = 0.0

    @property
    def last_check_duration(self):
        return self.last_check_end - self.last_check_start

    def run_blocking(self):
        self._loop.run_until_complete(self.run())

    async def run(self):
        while True:
            self.last_check_start = time.time()
            await self.check()
            self.last_check_end = time.time()
            await asyncio.sleep(self.interval - self.last_check_duration, loop=self._loop)

    async def check(self):
        raise NotImplementedError()

    def __repr__(self):
        return f"<{self.__class__.__qualname__} running every {self.interval} seconds>"
