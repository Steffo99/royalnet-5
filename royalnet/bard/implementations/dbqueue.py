from ..fileaudiosource import FileAudioSource
from ..discordbard import DiscordBard
from ..ytdldiscord import YtdlDiscord
from typing import List, AsyncGenerator, Tuple, Any, Dict, Optional


class DBQueue(DiscordBard):
    """A First-In-First-Out music queue.

    It is what was once called a ``playlist``."""
    def __init__(self):
        super().__init__()
        self.list: List[YtdlDiscord] = []

    async def _generator(self) -> AsyncGenerator[Optional[FileAudioSource], Tuple[Tuple[Any, ...], Dict[str, Any]]]:
        yield
        while True:
            try:
                ytd = self.list.pop(0)
            except IndexError:
                yield None
            else:
                async with ytd.spawn_audiosource() as fas:
                    yield fas

    async def add(self, ytd: YtdlDiscord):
        self.list.append(ytd)

    async def peek(self) -> List[YtdlDiscord]:
        return self.list

    async def remove(self, ytd: YtdlDiscord):
        self.list.remove(ytd)

    async def cleanup(self) -> None:
        for ytd in self.list:
            await ytd.delete_asap()
