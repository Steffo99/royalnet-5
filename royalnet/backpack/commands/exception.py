import royalnet
from royalnet.commands import *


class ExceptionCommand(Command):
    name: str = "exception"

    description: str = "Raise an exception in the command."

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        if not self.interface.cfg["exc_debug"]:
            raise UserError(f"{self.interface.prefix}{self.name} is not enabled.")
        raise Exception(f"{self.interface.prefix}{self.name} was called")
