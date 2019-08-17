import typing
from ..command import Command
from ..commandinterface import CommandInterface
from ..commandargs import CommandArgs
from ..commanddata import CommandData


class PingCommand(Command):
    name: str = "ping"

    description: str = "Replies with a Pong!"

    syntax: str = ""

    require_alchemy_tables: typing.Set = set()

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        await data.reply("Pong!")
