from ..database.tables import ActiveKvGroup, Royal, Keyvalue
from ..utils import Command, Call, asyncify


class KvCommand(Command):

    command_name = "kv"
    command_description = "Visualizza o modifica un valore rv."
    command_syntax = "(nomegruppo)"

    require_alchemy_tables = {ActiveKvGroup, Royal, Keyvalue}

    @classmethod
    async def common(cls, call: Call):
        key = call.args[0]
        value = call.args.optional(1)
        author = await call.get_author(error_if_none=True)
        active = await asyncify(call.session.query(call.alchemy.ActiveKvGroup).filter_by(royal=author).one_or_none)
        keyvalue = await asyncify(call.session.query(call.alchemy.Keyvalue).filter_by(group=active.group_name, key=key).one_or_none)
        if value is None:
            # Get
            if keyvalue is None:
                await call.reply("⚠️ La chiave specificata non esiste.")
                return
            await call.reply(f"ℹ️ Valore della chiave:\n{keyvalue}")
        else:
            # Set
            if keyvalue is None:
                keyvalue = call.alchemy.Keyvalue(group=active, key=key, value=value)
                call.session.add(keyvalue)
            else:
                keyvalue.value = value
            await asyncify(call.session.commit)
            await call.reply(f"✅ Chiave aggiornata:\n{keyvalue}")
