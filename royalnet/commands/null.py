from ..utils import Command, CommandArgs, Call


class NullCommand(Command):

    command_name = "null"
    command_description = "Non fa nulla."
    command_syntax = ""

    async def common(self, call: Call):
        pass
