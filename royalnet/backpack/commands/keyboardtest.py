from typing import *
from royalnet.commands import *
import functools
import asyncio


class KeyboardtestCommand(Command):
    name: str = "keyboardtest"

    description: str = "Create a new keyboard with the specified keys."

    syntax: str = "{keys}+"

    @staticmethod
    async def echo(data: CommandData, echo: str):
        await data.reply(echo)

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        keys = []
        for arg in args:
            # noinspection PyTypeChecker
            keys.append(KeyboardKey(interface=self.interface,
                                    short=arg[0],
                                    text=arg,
                                    callback=functools.partial(self.echo, echo=arg)))
        async with data.keyboard("This is a test keyboard.", keys):
            await asyncio.sleep(10)
        await data.reply("The keyboard is no longer in scope.")
