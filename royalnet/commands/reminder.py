import datetime
import dateparser
import typing
from ..utils import Command, Call, sleep_until


class ReminderCommand(Command):

    command_name = "reminder"
    command_description = "Ripete quello che gli avevi chiesto dopo un po' di tempo."
    command_syntax = "[ (data) ] (testo)"

    @classmethod
    async def common(cls, call: Call):
        match = call.args.match(r"\[ *(.+?) *] *(.+?) *$")
        date_str = match.group(1)
        reminder_text = match.group(2)
        date: typing.Optional[datetime.datetime]
        try:
            date = dateparser.parse(date_str)
        except OverflowError:
            date = None
        if date is None:
            await call.reply("⚠️ La data che hai inserito non è valida.")
        await call.reply(f"✅ Promemoria impostato per [b]{date.strftime('%Y-%m-%d %H:%M:%S')}[/b]")
        await sleep_until(date)
        await call.reply(f"❗️ Promemoria: [b]{reminder_text}[/b]")
