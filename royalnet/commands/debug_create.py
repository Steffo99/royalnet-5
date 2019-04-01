from ..utils import Command, CommandArgs, Call
from ..database.tables import Royal


class DebugCreateCommand(Command):

    command_name = "debug_create"
    command_title = "Create a new Royalnet user account"

    require_alchemy_tables = {Royal}

    async def common(self, call: Call, args: CommandArgs):
        royal = call.interface_alchemy.Royal(username=args[0], role="Member")
        call.session.add(royal)
        call.session.commit()
        await call.reply(f"✅ Utente <code>{royal}</code> creato!")
