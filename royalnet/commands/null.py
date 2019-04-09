from ..utils import Command, Call


class NullCommand(Command):

    command_name = "null"
    command_description = "Non fa nulla."
    command_syntax = ""

    @classmethod
    async def common(cls, call: Call):
        pass
