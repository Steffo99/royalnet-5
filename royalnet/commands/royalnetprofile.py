import asyncio
from ..utils import Command, Call
from ..database.tables import Royal, Telegram, Discord


class RoyalnetprofileCommand(Command):

    command_name = "royalnetprofile"
    command_description = "Invia in chat il link al tuo profilo Royalnet!"
    command_syntax = ""

    require_alchemy_tables = {Royal, Telegram, Discord}

    @classmethod
    async def common(cls, call: Call):
        author = await call.get_author(error_if_none=True)
        if author is None:
            await call.reply("⚠️ Devi essere registrato a Royalnet per usare questo comando!")
            return
        await call.reply(f"🔗 https://ryg.steffo.eu/profile/{author.username}")
