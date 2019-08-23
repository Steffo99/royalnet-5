import typing
from ..command import Command
from ..commandinterface import CommandInterface
from ..commandargs import CommandArgs
from ..commanddata import CommandData


class PingCommand(Command):
    name: str = "ping"

    description: str = "Replies with a Pong!"

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        await data.reply("🏓 Pong!")
