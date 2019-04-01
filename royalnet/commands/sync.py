import typing
from telegram import Update, User
from ..utils import Command, CommandArgs, Call, asyncify
from ..database.tables import Royal, Telegram


class SyncCommand(Command):

    command_name = "sync"
    command_title = "Connect your current account to Royalnet"

    require_alchemy_tables = [Royal, Telegram]

    async def common(self, call: Call, args: CommandArgs):
        raise NotImplementedError()

    async def telegram(self, call: Call, args: CommandArgs):
        update: Update = args.kwargs["update"]
        # Find the user
        user: typing.Optional[User] = update.effective_user
        if user is None:
            raise ValueError("Trying to sync a None user.")
        # Find the Royal
        royal = await asyncify(call.session.query(call.interface_alchemy.Royal).filter_by(username=args[0]).one_or_none)
        if royal is None:
            await call.reply("⚠️ Non esiste alcun account Royalnet con quel nome.")
        # Create a Telegram to connect to the Royal
        # Avatar is WIP
        telegram = call.interface_alchemy.Telegram(royal=royal,
                                                   tg_id=user.id,
                                                   tg_first_name=user.first_name,
                                                   tg_last_name=user.last_name,
                                                   tg_username=user.username)
        call.session.add(telegram)
        # Commit the session
        await asyncify(call.session.commit())
