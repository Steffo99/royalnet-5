import typing
import random
import dice
from royalnet.commands import *


class DiceCommand(Command):
    name: str = "dice"

    description: str = "Roll a dice, using 'dice'."

    aliases = ["d"]

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        ...
