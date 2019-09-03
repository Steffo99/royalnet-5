import typing
import random
from ..command import Command
from ..commandargs import CommandArgs
from ..commanddata import CommandData


class RageCommand(Command):
    name: str = "ship"

    description: str = "Arrabbiati per qualcosa, come una software house californiana."

    MAD = ["MADDEN MADDEN MADDEN MADDEN",
           "EA bad, praise Geraldo!",
           "Stai sfogando la tua ira sul bot!",
           "Basta, io cambio gilda!",
           "Fondiamo la RRYG!"]

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        await data.reply(f"😠 {random.sample(self.MAD, 1)[0]}")