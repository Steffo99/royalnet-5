import logging as _logging
from ..utils import Command, Call
from ..error import *

log = _logging.getLogger(__name__)


class ErrorHandlerCommand(Command):

    command_name = "error_handler"
    command_description = "Gestisce gli errori causati dagli altri comandi."
    command_syntax = ""

    @classmethod
    async def common(cls, call: Call):
        exception: Exception = call.kwargs["exception"]
        if isinstance(exception, NoneFoundError):
            await call.reply(f"⚠️ L'elemento richiesto non è stato trovato.\n[p]{exception}[/p]")
            return
        elif isinstance(exception, TooManyFoundError):
            await call.reply(f"⚠️ La richiesta effettuata è ambigua, pertanto è stata annullata.\n[p]{exception}[/p]")
            return
        elif isinstance(exception, UnregisteredError):
            await call.reply("⚠️ Devi essere registrato a Royalnet per usare questo comando.\nUsa il comando [c]sync[/c] per registrarti!")
            return
        elif isinstance(exception, UnsupportedError):
            await call.reply(f"⚠️ Il comando richiesto non è disponibile tramite l'interfaccia [c]{call.interface_name}[/c].")
            return
        elif isinstance(exception, InvalidInputError):
            command = call.kwargs["previous_command"]
            await call.reply(f"⚠️ Sintassi non valida.\nSintassi corretta: [c]{call.interface_prefix}{command.command_name} {command.command_syntax}[/c]")
            return
        elif isinstance(exception, InvalidConfigError):
            await call.reply(f"⚠️ Il bot non è stato configurato correttamente, quindi questo comando non può essere eseguito.\n[p]{exception}[/p]")
            return
        elif isinstance(exception, RoyalnetRequestError):
            await call.reply(f"⚠️ La richiesta a Royalnet ha restituito un errore:\n"
                             f"[p]{exception.error.extra_info['type']}\n"
                             f"{exception.error.extra_info['str']}[/p]")
            return
        elif isinstance(exception, ExternalError):
            await call.reply(f"⚠️ Una risorsa esterna necessaria per l'esecuzione del comando non ha funzionato correttamente, quindi il comando è stato annullato.\n[p]{exception}[/p]")
            return
        elif isinstance(exception, RoyalnetResponseError):
            log.warning(f"Invalid response from Royalnet - {exception.__class__.__name__}: {exception}")
            await call.reply(f"❌ La risposta ricevuta da Royalnet non è valida: [p]{exception}[/p]")
            return
        elif isinstance(exception, CurrentlyDisabledError):
            await call.reply(f"⚠️ Il comando richiesto è temporaneamente disabilitato.\n[p]{exception}[/p]")
            return
        elif __debug__:
            raise
        else:
            log.error(f"Unhandled exception - {exception.__class__.__name__}: {exception}")
            await call.reply(f"❌ Eccezione non gestita durante l'esecuzione del comando:\n[b]{exception.__class__.__name__}[/b]\n[p]{exception}[/p]")
