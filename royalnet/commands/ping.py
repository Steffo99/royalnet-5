from ..utils import Command, Call


class PingCommand(Command):

    command_name = "ping"
    command_title = "Ping pong!"

    async def common(self, call: Call, *args, **kwargs):
        await call.reply("Pong!")
