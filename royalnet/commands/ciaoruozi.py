from ..utils import Command, CommandArgs, Call
from telegram import Update, User


class CiaoruoziCommand(Command):

    command_name = "ciaoruozi"
    command_title = "Saluta Ruozi, anche se non è più in RYG."

    async def telegram(self, call: Call, args: CommandArgs):
        update: Update = args.kwargs["update"]
        user: User = update.effective_user
        if user.id == 112437036:
            await call.reply("Ciao me!")
        else:
            await call.reply("Ciao Ruozi!")
