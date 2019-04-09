import datetime
import dateparser
from ..utils import Command, Call, InvalidInputError


class DateparserCommand(Command):

    command_name = "dateparser"
    command_description = "Legge e comprende la data inserita."
    command_syntax = "(data)"

    @classmethod
    async def common(cls, call: Call):
        if len(call.args) == 0:
            raise InvalidInputError("Missing arg")
        text = " ".join(call.args)
        date: datetime.datetime = dateparser.parse(text)
        if date is None:
            await call.reply("🕕 La data inserita non è valida.")
            return
        await call.reply(f"🕐 La data inserita è {date.isoformat()}")
