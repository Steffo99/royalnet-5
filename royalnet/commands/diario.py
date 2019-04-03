import re
import datetime
from ..utils import Command, CommandArgs, Call, InvalidInputError
from ..database.tables import Royal, Diario, Alias


class DiarioCommand(Command):

    command_name = "diario"
    command_title = "Aggiungi una citazione al Diario."

    require_alchemy_tables = {Royal, Diario, Alias}

    async def common(self, call: Call, args: CommandArgs):
        # Recreate the full sentence
        text = " ".join(args)
        # Pass the sentence through the diario regex
        match = re.match(r'["«‘“‛‟❛❝〝＂`]([^"]+)["»’”❜❞〞＂`] *(?:(?:-{1,2}|—) *(\w+))?(?:,? *([^ ].*))?', text)
        # Find the corresponding matches
        if match is None:
            raise InvalidInputError("No match found.")
        text = match.group(1)
        quoted = match.group(2)
        context = match.group(3)
        timestamp = datetime.datetime.now()
        # Find if there's a Royalnet account associated with the quoted name
        quoted_alias = call.session.query(call.alchemy.Alias).filter_by(alias=quoted).one_or_none()
        quoted_account = quoted_alias.royal if quoted_alias is not None else None
        # Find the creator of the quote