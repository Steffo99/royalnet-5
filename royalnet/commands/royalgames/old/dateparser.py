import datetime
import dateparser
from ..utils import Command, Call


class DateparserCommand(Command):

    command_name = "dateparser"
    command_description = "Legge e comprende la data inserita."
    command_syntax = "(data)"

    @classmethod
    async def common(cls, call: Call):
        text = call.args.joined(require_at_least=1)
        date: datetime.datetime = dateparser.parse(text)
        if date is None:
            await call.reply("🕕 La data inserita non è valida.")
            return
        await call.reply(f"🕐 La data inserita è {date.strftime('%Y-%m-%d %H:%M:%S')}")
