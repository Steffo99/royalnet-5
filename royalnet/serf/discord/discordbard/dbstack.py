from typing import List, AsyncGenerator, Tuple, Any, Dict, Optional
from royalnet.bard import FileAudioSource, YtdlDiscord
from .discordbard import DiscordBard

try:
    import discord
except ImportError:
    discord = None


class DBStack(DiscordBard):
    """A First-In-Last-Out music queue.

    Not really sure if it is going to be useful..."""
    def __init__(self, voice_client: "discord.VoiceClient"):
        super().__init__(voice_client)
        self.list: List[YtdlDiscord] = []

    async def _generator(self) -> AsyncGenerator[Optional[FileAudioSource], Tuple[Tuple[Any, ...], Dict[str, Any]]]:
        yield
        while True:
            try:
                ytd = self.list.pop()
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
