import typing
from ..command import Command
from ..commandargs import CommandArgs
from ..commanddata import CommandData


class DebugKeyboardCommand(Command):
    name: str = "debug_keyboard"

    description: str = "Invia una tastiera di prova."

    async def _callback(self, data: CommandData):
        await data.reply("OK.")

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        await data.keyboard("This is a keyboard.", {
            "✅ OK": self._callback
        })
