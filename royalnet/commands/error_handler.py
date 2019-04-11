import traceback
from logging import Logger
from ..utils import Command, CommandArgs, Call, InvalidInputError, UnsupportedError, UnregisteredError


class ErrorHandlerCommand(Command):

    command_name = "error_handler"
    command_description = "Gestisce gli errori causati dagli altri comandi."
    command_syntax = ""

    @classmethod
    async def common(cls, call: Call):
        try:
            e_type, e_value, e_tb = call.kwargs["exception_info"]
        except InvalidInputError:
            await call.reply("⚠️ Questo comando non può essere chiamato da solo.")
            return
        if e_type == InvalidInputError:
            command = call.kwargs["previous_command"]
            await call.reply(f"⚠️ Sintassi non valida.\nSintassi corretta: [c]{call.interface_prefix}{command.command_name} {command.command_syntax}[/c]")
            return
        if e_type == UnregisteredError:
            await call.reply("⚠️ Devi essere registrato a Royalnet per usare questo comando!")
            return
        await call.reply(f"❌ Eccezione non gestita durante l'esecuzione del comando:\n[b]{e_type.__name__}[/b]\n{e_value}")
        formatted_tb: str = '\n'.join(traceback.format_tb(e_tb))
        call.logger.error(f"Unhandled exception - {e_type.__name__}: {e_value}\n{formatted_tb}")
