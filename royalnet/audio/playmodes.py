import math
import random
import typing
from .royalpcmaudio import RoyalPCMAudio


class PlayMode:
    def __init__(self):
        self.now_playing: typing.Optional[RoyalPCMAudio] = None
        self.generator: typing.AsyncGenerator = self._generator()

    async def next(self):
        return await self.generator.__anext__()

    def videos_left(self):
        raise NotImplementedError()

    async def _generator(self):
        """Get the next RPA from the list and advance it."""
        raise NotImplementedError()
        # This is needed to make the coroutine an async generator
        # noinspection PyUnreachableCode
        yield NotImplemented

    def add(self, item):
        """Add a new RPA to the PlayMode."""
        raise NotImplementedError()

    def delete(self):
        """Delete all RPAs contained inside this PlayMode."""


class Playlist(PlayMode):
    """A video list. RPAs played are removed from the list."""
    def __init__(self, starting_list: typing.List[RoyalPCMAudio] = None):
        super().__init__()
        if starting_list is None:
            starting_list = []
        self.list: typing.List[RoyalPCMAudio] = starting_list

    def videos_left(self):
        return len(self.list)

    async def _generator(self):
        while True:
            try:
                next_video = self.list.pop(0)
            except IndexError:
                self.now_playing = None
            else:
                self.now_playing = next_video
            yield self.now_playing
            if self.now_playing is not None:
                self.now_playing.delete()

    def add(self, item):
        self.list.append(item)

    def delete(self):
        while self.list:
            self.list.pop(0).delete()
        self.now_playing.delete()


class Pool(PlayMode):
    """A RPA pool. RPAs played are played back in random order, and they are kept in the pool."""
    def __init__(self, starting_pool: typing.List[RoyalPCMAudio] = None):
        super().__init__()
        if starting_pool is None:
            starting_pool = []
        self.pool: typing.List[RoyalPCMAudio] = starting_pool
        self._pool_copy: typing.List[RoyalPCMAudio] = []

    def videos_left(self):
        return math.inf

    async def _generator(self):
        while True:
            if not self.pool:
                self.now_playing = None
                yield None
                continue
            self._pool_copy = self.pool.copy()
            random.shuffle(self._pool_copy)
            while self._pool_copy:
                next_video = self._pool_copy.pop(0)
                self.now_playing = next_video
                yield next_video

    def add(self, item):
        self.pool.append(item)
        self._pool_copy.append(item)
        random.shuffle(self._pool_copy)

    def delete(self):
        for item in self.pool:
            item.delete()
        self.pool = None
        self._pool_copy = None
