from ..utils import Command, CommandArgs, Call, InvalidInputError


class ErrorHandlerCommand(Command):

    command_name = "error_handler"
    command_title = "Gestisce gli errori causati dagli altri comandi."
    command_syntax = ""

    async def telegram(self, call: Call, args: CommandArgs):
        try:
            exc = args.kwargs["exception"]
        except InvalidInputError:
            await call.reply("⚠️ Questo comando non può essere chiamato da solo.")
            return
        if isinstance(exc, InvalidInputError):
            command = args.kwargs["previous_command"]
            await call.reply(f"⚠️ Sintassi non valida.\nSintassi corretta:[c]/{command.command_name} {command.command_syntax}[/c]")
            return
        await call.reply("❌ Eccezione non gestita durante l'esecuzione del comando.")
