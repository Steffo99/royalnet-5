import math
import random


class PlayMode:
    def videos_left(self):
        raise NotImplementedError()

    async def next(self):
        """Get the next video from the list and advance it."""
        raise NotImplementedError()

    def add(self, item):
        """Add a new video to the PlayMode."""
        raise NotImplementedError()


class Playlist(PlayMode):
    """A video list. Videos played are removed from the list."""
    def __init__(self, starting_list=None):
        if starting_list is None:
            starting_list = []
        self.list = starting_list

    def videos_left(self):
        return len(self.list)

    async def next(self):
        while True:
            try:
                next_video = self.list.pop(0)
            except IndexError:
                yield None
            else:
                yield next_video

    def add(self, item):
        self.list.append(item)


class Pool(PlayMode):
    """A video pool. Videos played are played back in random order, and they are kept in the pool."""
    def __init__(self, starting_pool=None):
        if starting_pool is None:
            starting_pool = []
        self.pool = starting_pool
        self._pool_copy = []

    def videos_left(self):
        return math.inf

    async def next(self):
        while True:
            self._pool_copy = self.pool.copy()
            random.shuffle(self._pool_copy)
            while self._pool_copy:
                next_video = self._pool_copy.pop(0)
                yield next_video

    def add(self, item):
        self.pool.append(item)
        self._pool_copy.append(self._pool_copy)
        random.shuffle(self._pool_copy)
