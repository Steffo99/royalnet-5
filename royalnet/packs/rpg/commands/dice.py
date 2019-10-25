import dice
from royalnet.commands import *


class DiceCommand(Command):
    name: str = "dice"

    description: str = "Roll a dice, using 'dice'."

    syntax = "{dice}"

    aliases = ["d"]

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        dice_str = args.joined(require_at_least=1)
        try:
            roll = dice.roll(dice_str)
        except dice.DiceFatalException as e:
            raise CommandError(e.msg)
        except dice.DiceException as e:
            raise CommandError(e.msg)
        except dice.DiceBaseException as e:
            raise CommandError(str(e))
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
