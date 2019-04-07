from ..utils import Command, CommandArgs, Call


class PingCommand(Command):

    command_name = "ping"
    command_description = "Ping pong!"
    command_syntax = ""

    async def common(self, call: Call):
        await call.reply("🏓 Pong!")
