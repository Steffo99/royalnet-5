from ..utils import Command, CommandArgs, Call


class PingCommand(Command):

    command_name = "ping"
    command_title = "Ping pong!"
    command_syntax = ""

    async def common(self, call: Call, args: CommandArgs):
        await call.reply("🏓 Pong!")
