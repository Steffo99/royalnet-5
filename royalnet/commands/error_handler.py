import traceback
from ..utils import Command, Call
from ..error import NoneFoundError, \
                    TooManyFoundError, \
                    UnregisteredError, \
                    UnsupportedError, \
                    InvalidInputError, \
                    InvalidConfigError, \
                    ExternalError


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
        if e_type == NoneFoundError:
            await call.reply("⚠️ L'elemento richiesto non è stato trovato.")
            return
        if e_type == TooManyFoundError:
            await call.reply("⚠️ La richiesta effettuata è ambigua, pertanto è stata annullata.")
            return
        if e_type == UnregisteredError:
            await call.reply("⚠️ Devi essere registrato a Royalnet per usare questo comando!")
            return
        if e_type == UnsupportedError:
            await call.reply("⚠️ Il comando richiesto non è disponibile tramite questa interfaccia.")
            return
        if e_type == InvalidInputError:
            command = call.kwargs["previous_command"]
            await call.reply(f"⚠️ Sintassi non valida.\nSintassi corretta: [c]{call.interface_prefix}{command.command_name} {command.command_syntax}[/c]")
            return
        if e_type == InvalidConfigError:
            await call.reply("⚠️ Il bot non è stato configurato correttamente, quindi questo comando non può essere eseguito. L'errore è stato segnalato all'amministratore.")
            return
        if e_type == ExternalError:
            await call.reply("⚠️ Una risorsa esterna necessaria per l'esecuzione del comando non ha funzionato correttamente, quindi il comando è stato annullato.")
            return
        await call.reply(f"❌ Eccezione non gestita durante l'esecuzione del comando:\n[b]{e_type.__name__}[/b]\n{e_value}")
        formatted_tb: str = '\n'.join(traceback.format_tb(e_tb))
        call.logger.error(f"Unhandled exception - {e_type.__name__}: {e_value}\n{formatted_tb}")
