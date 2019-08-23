from ..utils import Command, Call


class ColorCommand(Command):

    command_name = "color"
    command_description = "Invia un colore in chat...?"
    command_syntax = ""

    @classmethod
    async def common(cls, call: Call):
        await call.reply("""
        [i]I am sorry, unknown error occured during working with your request, Admin were notified[/i]
        """)
