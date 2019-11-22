from typing import Optional, List, AsyncGenerator, Tuple, Any, Dict
from royalnet.bard import YtdlDiscord
from .playable import Playable
try:
    import discord
except ImportError:
    discord = None


class PlayableYTDQueue(Playable):
    """A queue of :class:`YtdlDiscord` to be played in sequence."""
    def __init__(self, start_with: Optional[List[YtdlDiscord]] = None):
        super().__init__()
        self.contents: List[YtdlDiscord] = []
        if start_with is not None:
            self.contents = [*self.contents, *start_with]

    async def _generator(self) \
            -> AsyncGenerator[Optional["discord.AudioSource"], Tuple[Tuple[Any, ...], Dict[str, Any]]]:
        yield
        while True:
            try:
                # Try to get the first YtdlDiscord of the queue
                ytd: YtdlDiscord = self.contents.pop(0)
            except IndexError:
                # If there isn't anything, yield None
                yield None
                continue
            try:
                # Create a FileAudioSource from the YtdlDiscord
                # If the file hasn't been fetched / downloaded / converted yet, it will do so before yielding
                async with ytd.spawn_audiosource() as fas:
                    # Yield the resulting AudioSource
                    yield fas
            finally:
                # Delete the YtdlDiscord file
                await ytd.delete_asap()
