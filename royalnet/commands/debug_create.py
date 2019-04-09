from ..utils import Command, Call, asyncify
from ..database.tables import Royal, Alias


class DebugCreateCommand(Command):

    command_name = "debug_create"
    command_description = "Crea un nuovo account Royalnet"
    command_syntax = "(newusername)"

    require_alchemy_tables = {Royal, Alias}

    @classmethod
    async def common(cls, call: Call):
        royal = call.alchemy.Royal(username=call.args[0], role="Member")
        call.session.add(royal)
        alias = call.alchemy.Alias(royal=royal, alias=royal.username.lower())
        call.session.add(alias)
        await asyncify(call.session.commit)
        await call.reply(f"✅ Utente {royal} creato!")
