import royalnet
from royalnet.commands import *


class ExceventCommand(Command):
    name: str = "excevent"

    description: str = "Call an event that raises an exception."

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        if not self.interface.cfg["exc_debug"]:
            raise UserError(f"{self.interface.prefix}{self.name} is not enabled.")
        await self.interface.call_herald_event(self.interface.name, "exception")
        await data.reply("✅ Event called!")
