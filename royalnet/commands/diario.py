from ..utils import Command, CommandArgs, Call


class DiarioCommand(Command):

    command_name = "diario"
    command_title = "Aggiungi una citazione al Diario."

    async def common(self, call: Call, args: CommandArgs):
        # TODO
        raise NotImplementedError("TODO")
