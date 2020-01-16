import royalnet
from royalnet.commands import *


class ExceptionCommand(Command):
    name: str = "exception"

    description: str = "Raise an exception in the command."

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        raise Exception(f"{self.interface.prefix}{self.name} was called")
