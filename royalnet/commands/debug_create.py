from ..utils import Command, CommandArgs, Call, asyncify
from ..database.tables import Royal, Alias


class DebugCreateCommand(Command):

    command_name = "debug_create"
    command_title = "Crea un nuovo account Royalnet"
    command_syntax = "(newusername)"

    require_alchemy_tables = {Royal, Alias}

    async def common(self, call: Call, args: CommandArgs):
        royal = call.alchemy.Royal(username=args[0], role="Member")
        call.session.add(royal)
        alias = call.alchemy.Alias(royal=royal, alias=royal.username)
        call.session.add(alias)
        await asyncify(call.session.commit)
        await call.reply(f"✅ Utente <code>{royal}</code> creato!")
