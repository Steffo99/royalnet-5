import typing
from ..command import Command
from ..commandargs import CommandArgs
from ..commanddata import CommandData


class DebugInvokingCommand(Command):
    name: str = "debug_invoking"

    description: str = "Elimina il messaggio di invocazione."

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        await data.delete_invoking(error_if_unavailable=True)
        await data.reply("🗑 Messaggio eliminato.")
