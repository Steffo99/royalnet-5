import typing
import random
from royalnet.commands import *


class RollCommand(Command):
    name: str = "roll"

    description: str = "Roll a dice, from N to M (defaults to 1-100)."

    syntax = "[min] [max]"

    aliases = ["r", "random"]

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        first: typing.Optional[str] = args.optional(0)
        second: typing.Optional[str] = args.optional(1)
        if second:
            minimum = int(first)
            maximum = int(second)
        elif first:
            minimum = 1
            maximum = int(first)
        else:
            minimum = 1
            maximum = 100
        result = random.randrange(minimum, maximum+1)
        await data.reply(f"🎲 Dice roll [{minimum}-{maximum}]: [b]{result}[/b]")
