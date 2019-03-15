from ..utils import Command, CommandArgs, Call


class NullCommand(Command):

    command_name = "null"
    command_title = "Do nothing"

    async def common(self, call: Call, args: CommandArgs):
        pass
