import typing
from ..command import Command
from ..commandargs import CommandArgs
from ..commanddata import CommandData


class DebugErrorCommand(Command):
    name: str = "debug_error"

    description: str = "Causa un'eccezione nel bot."

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        raise Exception("debug_error command was called")
