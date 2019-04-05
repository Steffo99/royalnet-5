import typing
from telegram import Update, User
from ..utils import Command, CommandArgs, Call, asyncify, UnsupportedError
from ..database.tables import Royal, Telegram


class SyncCommand(Command):

    command_name = "sync"
    command_title = "Connetti il tuo account attuale a Royalnet!"
    command_syntax = "(royalnetusername)"

    require_alchemy_tables = {Royal, Telegram}

    async def common(self, call: Call):
        raise UnsupportedError()

    async def telegram(self, call: Call):
        update: Update = call.kwargs["update"]
        # Find the user
        user: typing.Optional[User] = update.effective_user
        if user is None:
            raise ValueError("Trying to sync a None user.")
        # Find the Royal
        royal = await asyncify(call.session.query(call.alchemy.Royal).filter_by(username=call.args[0]).one_or_none)
        if royal is None:
            await call.reply("⚠️ Non esiste alcun account Royalnet con quel nome.")
            return
        # Find if the user is already synced
        telegram = await asyncify(call.session.query(call.alchemy.Telegram).filter_by(tg_id=user.id).one_or_none)
        if telegram is None:
            # Create a Telegram to connect to the Royal
            # Avatar is WIP
            telegram = call.alchemy.Telegram(royal=royal,
                                             tg_id=user.id,
                                             tg_first_name=user.first_name,
                                             tg_last_name=user.last_name,
                                             tg_username=user.username)
            call.session.add(telegram)
            await call.reply(f"✅ Connessione completata: {str(royal)} ⬌ {str(telegram)}")
        else:
            # Update the Telegram data
            # Avatar is WIP
            telegram.tg_first_name = user.first_name
            telegram.tg_last_name = user.last_name
            telegram.tg_username = user.username
            await call.reply(f"✅ Dati di {str(telegram)} aggiornati.")
        # Commit the session
        await asyncify(call.session.commit)
