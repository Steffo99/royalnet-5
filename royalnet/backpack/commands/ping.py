from royalnet.commands import *


class PingCommand(Command):
    name: str = "ping"

    description: str = "Get a pong response."

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        await data.reply("🏓 Pong!")
