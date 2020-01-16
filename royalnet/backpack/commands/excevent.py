import royalnet
from royalnet.commands import *


class ExceventCommand(Command):
    name: str = "excevent"

    description: str = "Call an event that raises an exception."

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        await self.interface.call_herald_event(self.interface.name, "exception")
        await data.reply("✅ Event called!")
