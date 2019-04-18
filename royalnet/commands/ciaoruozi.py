from ..utils import Command, Call
from telegram import Update, User


class CiaoruoziCommand(Command):

    command_name = "ciaoruozi"
    command_description = "Saluta Ruozi, anche se non è più in RYG."
    command_syntax = ""

    @classmethod
    async def common(cls, call: "Call"):
        await call.reply("👋 Ciao Ruozi!")

    @classmethod
    async def telegram(cls, call: Call):
        update: Update = call.kwargs["update"]
        user: User = update.effective_user
        if user.id == 112437036:
            await call.reply("👋 Ciao me!")
        else:
            await call.reply("👋 Ciao Ruozi!")
