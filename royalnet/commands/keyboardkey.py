from typing import *
from .commandinterface import CommandInterface
from .commanddata import CommandData


class KeyboardKey:
    def __init__(self,
                 interface: CommandInterface,
                 short: str,
                 text: str,
                 callback: Callable[[CommandData], Awaitable[None]]):
        self.interface: CommandInterface = interface
        self.short: str = short
        self.text: str = text
        self.callback: Callable[[CommandData], Awaitable[None]] = callback

    async def press(self, data: CommandData):
        await self.callback(data)
