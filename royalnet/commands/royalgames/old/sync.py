import typing
from telegram import Update, User
from discord import Message, Member
from ..utils import Command, Call, asyncify
from ..error import UnsupportedError
from ..database.tables import Royal, Telegram, Discord


class SyncCommand(Command):

    command_name = "sync"
    command_description = "Connetti il tuo account attuale a Royalnet!"
    command_syntax = "(royalnetusername)"

    require_alchemy_tables = {Royal, Telegram, Discord}

    @classmethod
    async def common(cls, call: Call):
        raise UnsupportedError()

    @classmethod
    async def telegram(cls, call: Call):
        update: Update = call.kwargs["update"]
        # Find the user
        user: typing.Optional[User] = update.effective_user
        if user is None:
            raise ValueError("Trying to sync a None user.")
        # Find the Royal
        royal = await asyncify(call.session.query(call.alchemy.Royal).filter_by(username=call.args[0]).one_or_none)
        if royal is None:
            await call.reply("⚠️ Non esiste alcun account Royalnet con quel nome. Ricorda, gli username sono [b]case-sensitive[/b]!")
            return
        # Find if the user is already synced
        telegram = await asyncify(call.session.query(call.alchemy.Telegram).filter_by(tg_id=user.id).one_or_none)
        if telegram is None:
            # Create a Telegram to connect to the Royal
            # Avatar is WIP
            telegram = call.alchemy.Telegram(royal=royal,
                                             tg_id=user.id,
                                             first_name=user.first_name,
                                             last_name=user.last_name,
                                             username=user.username)
            call.session.add(telegram)
            await call.reply(f"✅ Connessione completata: {str(royal)} ⬌ {str(telegram)}")
        else:
            # Update the Telegram data
            telegram.first_name = user.first_name
            telegram.last_name = user.last_name
            telegram.username = user.username
            await call.reply(f"✅ Connessione aggiornata: {str(royal)} ⬌ {str(telegram)}")
        # Commit the session
        await asyncify(call.session.commit)

    @classmethod
    async def discord(cls, call: Call):
        message: Message = call.kwargs["message"]
        user: typing.Optional[Member] = message.author
        # Find the Royal
        royal = await asyncify(call.session.query(call.alchemy.Royal).filter_by(username=call.args[0]).one_or_none)
        if royal is None:
            await call.reply("⚠️ Non esiste alcun account Royalnet con quel nome. Ricorda, gli username sono [b]case-sensitive[/b]!")
            return
        # Find if the user is already synced
        discord = await asyncify(call.session.query(call.alchemy.Discord).filter_by(discord_id=user.id).one_or_none)
        if discord is None:
            # Create a Discord to connect to the Royal
            discord = call.alchemy.Discord(royal=royal,
                                           discord_id=user.id,
                                           username=user.name,
                                           discriminator=user.discriminator,
                                           avatar_hash=user.avatar)
            call.session.add(discord)
            await call.reply(f"✅ Connessione completata: {str(royal)} ⬌ {str(discord)}")
        else:
            # Update the Discord data
            discord.username = user.name
            discord.discriminator = user.discriminator
            discord.avatar_hash = user.avatar
            await call.reply(f"✅ Connessione aggiornata: {str(royal)} ⬌ {str(discord)}")
        # Commit the session
        await asyncify(call.session.commit)
