import random
from ..database.tables import ActiveKvGroup, Royal, Keygroup, Keyvalue
from ..utils import Command, Call, asyncify, plusformat


class KvrollCommand(Command):

    command_name = "kvroll"
    command_description = "Lancia 1d20, poi aggiungici il valore della kv selezionata."
    command_syntax = "(chiave) [modifier]"

    require_alchemy_tables = {ActiveKvGroup, Royal, Keyvalue, Keygroup}

    @classmethod
    async def common(cls, call: Call):
        key = call.args[0].lower()
        normal_mod_str = call.args.optional(1, 0)
        try:
            normal_modifier = int(normal_mod_str)
        except ValueError:
            await call.reply("⚠️ Il modificatore specificato non è un numero.")
            return
        author = await call.get_author(error_if_none=True)
        active = await asyncify(call.session.query(call.alchemy.ActiveKvGroup).filter_by(royal=author).one_or_none)
        if active is None:
            await call.reply("⚠️ Devi prima attivare un gruppo con il comando [c]kvactive[/c]!")
            return
        keyvalue = await asyncify(call.session.query(call.alchemy.Keyvalue).filter_by(group=active.group, key=key).one_or_none)
        if keyvalue is None:
            await call.reply("⚠️ La chiave specificata non esiste.")
            return
        try:
            kv_modifier = int(keyvalue.value)
        except ValueError:
            await call.reply("⚠️ Il valore della chiave specificata non è un numero.")
            return
        roll = random.randrange(1, 21)
        result = roll + kv_modifier + normal_modifier
        await call.reply(f"🎲 {roll}{plusformat(kv_modifier)}{plusformat(normal_modifier)} = [b]{result}[/b]")
