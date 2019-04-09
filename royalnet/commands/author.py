from ..utils import Command, Call
from ..database.tables import Royal, Telegram


class AuthorCommand(Command):

    command_name = "author"
    command_description = "Ottieni informazioni sull'autore di questa chiamata."
    command_syntax = ""

    require_alchemy_tables = {Royal, Telegram}

    @classmethod
    async def common(cls, call: Call):
        author = await call.get_author()
        if author is None:
            await call.reply(f"☁️ L'autore di questa chiamata è sconosciuto.")
        await call.reply(f"🌞 {str(author)} è l'autore di questa chiamata.")
