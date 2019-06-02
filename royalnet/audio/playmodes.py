import math
import random
import typing
from .royalpcmaudio import RoyalPCMAudio


class PlayMode:
    """The base class for a PlayMode, such as :py:class:`royalnet.audio.Playlist`. Inherit from this class if you want to create a custom PlayMode."""

    def __init__(self):
        """Create a new PlayMode and initialize the generator inside."""
        self.now_playing: typing.Optional[RoyalPCMAudio] = None
        self.generator: typing.AsyncGenerator = self._generate_generator()

    async def next(self) -> typing.Optional[RoyalPCMAudio]:
        """Get the next :py:class:`royalnet.audio.RoyalPCMAudio` from the list and advance it.

        Returns:
            The next :py:class:`royalnet.audio.RoyalPCMAudio`."""
        return await self.generator.__anext__()

    def videos_left(self) -> typing.Union[int, float]:
        """Return the number of videos left in the PlayMode.

        Returns:
            Usually a :py:class:`int`, but may return also :py:obj:`math.inf` if the PlayMode is infinite."""
        raise NotImplementedError()

    async def _generate_generator(self):
        """Factory function for an async generator that changes the ``now_playing`` property either to a :py:class:`discord.audio.RoyalPCMAudio` or to ``None``, then yields the value it changed it to.

        Yields:
            The :py:class:`royalnet.audio.RoyalPCMAudio` to be played next."""
        raise NotImplementedError()
        # This is needed to make the coroutine an async generator
        # noinspection PyUnreachableCode
        yield NotImplemented

    def add(self, item: RoyalPCMAudio) -> None:
        """Add a new :py:class:`royalnet.audio.RoyalPCMAudio` to the PlayMode.

        Args:
            item: The item to add to the PlayMode."""
        raise NotImplementedError()

    def delete(self) -> None:
        """Delete all :py:class:`royalnet.audio.RoyalPCMAudio` contained inside this PlayMode."""
        raise NotImplementedError()

    def queue_preview(self) -> typing.List[RoyalPCMAudio]:
        """Display all the videos in the PlayMode as a list, if possible.

        To be used with `queue` commands, for example.

        Raises:
            NotImplementedError: If a preview can't be generated.

        Returns:
            A list of videos contained in the queue."""
        raise NotImplementedError()


class Playlist(PlayMode):
    """A video list. :py:class:`royalnet.audio.RoyalPCMAudio` played are removed from the list."""

    def __init__(self, starting_list: typing.List[RoyalPCMAudio] = None):
        """Create a new Playlist.

        Args:
            starting_list: A list of items with which the Playlist will be created."""
        super().__init__()
        if starting_list is None:
            starting_list = []
        self.list: typing.List[RoyalPCMAudio] = starting_list

    def videos_left(self) -> typing.Union[int, float]:
        return len(self.list)

    async def _generate_generator(self):
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

    def add(self, item) -> None:
        self.list.append(item)

    def delete(self) -> None:
        if self.now_playing is not None:
            self.now_playing.delete()
        while self.list:
            self.list.pop(0).delete()

    def queue_preview(self) -> typing.List[RoyalPCMAudio]:
        return self.list


class Pool(PlayMode):
    """A :py:class:`royalnet.audio.RoyalPCMAudio` pool. :py:class:`royalnet.audio.RoyalPCMAudio` are selected in random order and are not repeated until every song has been played at least once."""

    def __init__(self, starting_pool: typing.List[RoyalPCMAudio] = None):
        """Create a new Pool.

        Args:
            starting_pool: A list of items the Pool will be created from."""
        super().__init__()
        if starting_pool is None:
            starting_pool = []
        self.pool: typing.List[RoyalPCMAudio] = starting_pool
        self._pool_copy: typing.List[RoyalPCMAudio] = []

    def videos_left(self) -> typing.Union[int, float]:
        return math.inf

    async def _generate_generator(self):
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

    def add(self, item) -> None:
        self.pool.append(item)
        self._pool_copy.append(item)
        random.shuffle(self._pool_copy)

    def delete(self) -> None:
        for item in self.pool:
            item.delete()
        self.pool = None
        self._pool_copy = None

    def queue_preview(self) -> typing.List[RoyalPCMAudio]:
        preview_pool = self.pool.copy()
        random.shuffle(preview_pool)
        return preview_pool