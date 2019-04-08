import random
from ..utils import Command, Call


MAD = ["MADDEN MADDEN MADDEN MADDEN",
       "EA bad, praise Geraldo!",
       "Stai sfogando la tua ira sul bot!",
       "Basta, io cambio gilda!",
       "Fondiamo la RRYG!"]


class RageCommand(Command):

    command_name = "rage"
    command_description = "Arrabbiati con qualcosa, possibilmente una software house."
    command_syntax = ""

    @classmethod
    async def common(cls, call: Call):
        await call.reply(f"😠 {random.sample(MAD, 1)[0]}")
