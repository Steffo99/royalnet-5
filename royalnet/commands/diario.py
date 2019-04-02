from ..utils import Command, CommandArgs, Call
import re


class DiarioCommand(Command):

    command_name = "diario"
    command_title = "Aggiungi una citazione al Diario."

    async def common(self, call: Call, args: CommandArgs):
        # Recreate the full sentence
        text = " ".join(args)
        # Pass the sentence through the diario regex
        match = re.match(r'["«‘“‛‟❛❝〝＂`]([^"]+)["»’”❜❞〞＂`] *(?:(?:-{1,2}|—) *(\w+))?(?:,? *([^ ].*))?', text)
        # TODO