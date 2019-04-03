import re
import datetime
from ..utils import Command, CommandArgs, Call, InvalidInputError
from ..database.tables import Royal, Diario, Alias
from ..utils import asyncify


class DiarioCommand(Command):

    command_name = "diario"
    command_title = "Aggiungi una citazione al Diario."

    require_alchemy_tables = {Royal, Diario, Alias}

    async def common(self, call: Call, args: CommandArgs):
        # Recreate the full sentence
        text = " ".join(args.args)
        # Pass the sentence through the diario regex
        match = re.match(r'(!)? *["«‘“‛‟❛❝〝＂`]([^"]+)["»’”❜❞〞＂`] *(?:(?:-{1,2}|—) *([\w ]+))?(?:, *([^ ].*))?', text)
        # Find the corresponding matches
        if match is None:
            await call.reply(f"✅ Comando skippato per frase non valida")
            raise InvalidInputError("No match found.")
        spoiler = bool(match.group(1))
        text = match.group(2)
        quoted = match.group(3)
        context = match.group(4)
        timestamp = datetime.datetime.now()
        # Find if there's a Royalnet account associated with the quoted name
        if quoted is not None:
            quoted_alias = await asyncify(call.session.query(call.alchemy.Alias).filter_by(alias=quoted.lower()).one_or_none)
        else:
            quoted_alias = None
        quoted_account = quoted_alias.royal if quoted_alias is not None else None
        # Find the creator of the quotes
        creator = await call.get_author()
        # Create the diario quote
        diario = call.alchemy.Diario(creator=creator,
                                     quoted_account=quoted_account,
                                     quoted=quoted,
                                     text=text,
                                     context=context,
                                     timestamp=timestamp,
                                     media_url=None,
                                     spoiler=spoiler)
        call.session.add(diario)
        await asyncify(call.session.commit)
        await call.reply(f"✅ Aggiunto al diario: <code>{repr(diario)}</code>")
