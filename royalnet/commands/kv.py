from ..database.tables import ActiveKvGroup, Royal, Keyvalue, Keygroup
from ..utils import Command, Call, asyncify


class KvCommand(Command):

    command_name = "kv"
    command_description = "Visualizza o modifica un valore kv."
    command_syntax = "(chiave) [valore]"

    require_alchemy_tables = {ActiveKvGroup, Royal, Keyvalue, Keygroup}

    @classmethod
    async def common(cls, call: Call):
        key = call.args[0].lower()
        value = call.args.optional(1)
        author = await call.get_author(error_if_none=True)
        active = await asyncify(call.session.query(call.alchemy.ActiveKvGroup).filter_by(royal=author).one_or_none)
        if active is None:
            await call.reply("⚠️ Devi prima attivare un gruppo con il comando [c]kvactive[/c]!")
            return
        keyvalue = await asyncify(call.session.query(call.alchemy.Keyvalue).filter_by(group=active.group, key=key).one_or_none)
        if value is None:
            # Get
            if keyvalue is None:
                await call.reply("⚠️ La chiave specificata non esiste.")
                return
            await call.reply(f"ℹ️ Valore della chiave:\n{keyvalue}")
        else:
            # Set/kv asdf 1000
            if keyvalue is None:
                keyvalue = call.alchemy.Keyvalue(group=active.group, key=key, value=value)
                call.session.add(keyvalue)
            else:
                keyvalue.value = value
            await asyncify(call.session.commit)
            await call.reply(f"✅ Chiave aggiornata:\n{keyvalue}")
