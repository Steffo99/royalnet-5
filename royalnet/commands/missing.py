import asyncio
import logging as _logging
from ..utils import Command, Call

loop = asyncio.get_event_loop()
log = _logging.getLogger(__name__)


class MissingCommand(Command):

    command_name = "missing"
    command_description = "Informa che il comando non esiste."
    command_syntax = ""

    @classmethod
    async def common(cls, call: Call):
        await call.reply(f"⚠️ Il comando richiesto non esiste.")
