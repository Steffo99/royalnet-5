from typing import *

from .commanddata import CommandData


class KeyboardKey:
    def __init__(self,
                 short: str,
                 text: str,
                 callback: Callable[[CommandData], Awaitable[None]]):
        self.short: str = short
        self.text: str = text
        self.callback: Callable[[CommandData], Awaitable[None]] = callback

    async def press(self, data: CommandData):
        await self.callback(data)
