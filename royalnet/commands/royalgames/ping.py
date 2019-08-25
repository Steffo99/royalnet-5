import typing
from ..command import Command
from ..commandargs import CommandArgs
from ..commanddata import CommandData


class PingCommand(Command):
    name: str = "ping"

    description: str = "Gioca a ping-pong con il bot."

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        await data.reply("🏓 Pong!")
