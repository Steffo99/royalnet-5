from royalnet.bard import FileAudioSource
from typing import List, AsyncGenerator, Tuple, Any, Dict, Optional
from .discordbard import DiscordBard
from .ytdldiscord import YtdlDiscord

try:
    import discord
except ImportError:
    discord = None


class DBQueue(DiscordBard):
    """A First-In-First-Out music queue.

    It is what was once called a ``playlist``."""
    def __init__(self, voice_client: "discord.VoiceClient"):
        super().__init__(voice_client)
        self.list: List[YtdlDiscord] = []

    async def _generator(self) -> AsyncGenerator[Optional[FileAudioSource], Tuple[Tuple[Any, ...], Dict[str, Any]]]:
        yield
        while True:
            try:
                ytd = self.list.pop(0)
            except IndexError:
                yield None
            else:
                try:
                    async with ytd.spawn_audiosource() as fas:
                        yield fas
                finally:
                    await ytd.delete_asap()

    async def add(self, ytd: YtdlDiscord):
        self.list.append(ytd)

    async def peek(self) -> List[YtdlDiscord]:
        return self.list

    async def remove(self, ytd: YtdlDiscord):
        self.list.remove(ytd)

    async def cleanup(self) -> None:
        for ytd in self.list:
            await ytd.delete_asap()
        await self.stop()
