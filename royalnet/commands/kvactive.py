from ..database.tables import ActiveKvGroup, Royal, Keygroup
from ..utils import Command, Call, asyncify


class KvactiveCommand(Command):

    command_name = "kvactive"
    command_description = "Seleziona un gruppo di valori kv."
    command_syntax = "(nomegruppo)"

    require_alchemy_tables = {ActiveKvGroup, Royal, Keygroup}

    @classmethod
    async def common(cls, call: Call):
        group_name = call.args[0].lower()
        author = await call.get_author(error_if_none=True)
        active = await asyncify(call.session.query(call.alchemy.ActiveKvGroup).filter_by(royal=author).one_or_none)
        if active is None:
            group = await asyncify(call.session.query(call.alchemy.Keygroup).filter_by(group_name=group_name).one_or_none)
            if group is None:
                group = call.alchemy.Keygroup(group_name=group_name)
                call.session.add(group)
            active = call.alchemy.ActiveKvGroup(royal=author, group=group)
            call.session.add(active)
        else:
            group = await asyncify(call.session.query(call.alchemy.Keygroup).filter_by(group_name=group_name).one_or_none)
            if group is None:
                group = call.alchemy.Keygroup(group_name=group_name)
                call.session.add(group)
            active.group = group
        await asyncify(call.session.commit)
        await call.reply(f"✅ Hai attivato il gruppo [b]{group_name}[/b].")
