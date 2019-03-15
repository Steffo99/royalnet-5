from ..utils import Command, Call


class PingCommand(Command):
    async def common(self, call: Call, *args, **kwargs):
        await call.reply("Pong!")
