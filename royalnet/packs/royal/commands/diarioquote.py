from royalnet.commands import *
from royalnet.utils import *
from ..tables import Diario


class DiarioquoteCommand(Command):
    name: str = "diarioquote"

    description: str = "Cita una riga del diario."

    aliases = ["dq", "quote", "dquote"]

    syntax = "{id}"

    tables = {Diario}

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        try:
            entry_id = int(args[0].lstrip("#"))
        except ValueError:
            raise CommandError("L'id che hai specificato non è valido.")
        entry: Diario = await asyncify(data.session.query(self.alchemy.Diario).get, entry_id)
        if entry is None:
            raise CommandError("Nessuna riga con quell'id trovata.")
        await data.reply(str(entry))
