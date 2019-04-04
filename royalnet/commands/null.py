from ..utils import Command, CommandArgs, Call


class NullCommand(Command):

    command_name = "null"
    command_title = "Non fa nulla."
    command_syntax = ""

    async def common(self, call: Call, args: CommandArgs):
        pass
