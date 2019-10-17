from royalnet.commands import *


class ColorCommand(Command):
    name: str = "color"

    description: str = "Invia un colore in chat...?"

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        await data.reply("""
                         [i]I am sorry, unknown error occured during working with your request, Admin were notified[/i]
                         """)
