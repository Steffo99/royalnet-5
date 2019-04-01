from ..utils import Command, CommandArgs, Call


class ColorCommand(Command):

    command_name = "color"
    command_title = "Invia un colore in chat...?"

    async def common(self, call: Call, args: CommandArgs):
        await call.reply("""
        <i>I am sorry, unknown error occured during working with your request, Admin were notified</i>
        """)
