import logging
from typing import Optional, List, AsyncGenerator, Tuple, Any, Dict
from royalnet.bard import YtdlDiscord
from .playable import Playable
try:
    import discord
except ImportError:
    discord = None


log = logging.getLogger(__name__)


class PlayableYTDQueue(Playable):
    """A queue of :class:`YtdlDiscord` to be played in sequence."""
    def __init__(self, start_with: Optional[List[YtdlDiscord]] = None):
        super().__init__()
        self.contents: List[YtdlDiscord] = []
        self.now_playing: Optional[YtdlDiscord] = None
        if start_with is not None:
            self.contents = [*self.contents, *start_with]
        log.debug(f"Created new PlayableYTDQueue containing: {self.contents}")

    async def _generator(self) \
            -> AsyncGenerator[Optional["discord.AudioSource"], Tuple[Tuple[Any, ...], Dict[str, Any]]]:
        yield
        while True:
            log.debug(f"Dequeuing an item...")
            try:
                # Try to get the first YtdlDiscord of the queue
                self.now_playing: YtdlDiscord = self.contents.pop(0)
            except IndexError:
                # If there isn't anything, yield None
                log.debug(f"Nothing to dequeue, yielding None.")
                yield None
                continue
            log.debug(f"Yielding FileAudioSource from: {self.now_playing}")
            # Create a FileAudioSource from the YtdlDiscord
            # If the file hasn't been fetched / downloaded / converted yet, it will do so before yielding
            async with self.now_playing.spawn_audiosource() as fas:
                # Yield the resulting AudioSource
                yield fas
            # Delete the YtdlDiscord file
            log.debug(f"Deleting: {self.now_playing}")
            await self.now_playing.delete_asap()
            log.debug(f"Deleted successfully!")
