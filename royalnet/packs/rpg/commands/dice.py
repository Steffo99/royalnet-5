import dice
from royalnet.commands import *


class DiceCommand(Command):
    name: str = "dice"

    description: str = "Roll a dice, using 'dice'."

    aliases = ["d"]

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        dice_str = args.joined(require_at_least=1)
        roll = dice.roll(dice_str)
        try:
            result = list(roll)
        except TypeError:
            result = [roll]
        message = f"🎲 {dice_str}"
        total = 0
        if len(result) > 1:
            message += f" = "
            for index, die in enumerate(result):
                message += f"{die}"
                total += int(die)
                if (index + 1) < len(result):
                    message += "+"
        else:
            total += int(result[0])
        message += f" = [b]{total}[/b]"
        await data.reply(message)
