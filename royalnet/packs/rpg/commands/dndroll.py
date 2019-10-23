import typing
import random
from royalnet.commands import *
from royalnet.utils import plusformat
from ..tables import DndCharacter, DndActiveCharacter


class DndrollCommand(Command):
    name: str = "dndroll"

    description: str = "Roll as the active DnD character."

    aliases = ["dr", "dndr", "droll"]

    syntax = "{stat} [proficiency] [modifier]"

    tables = {DndCharacter, DndActiveCharacter}

    @staticmethod
    def _roll():
        return random.randrange(1, 21)

    _roll_string = "1d20"

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        author = await data.get_author(error_if_none=True)
        if author.dnd_active_character is None:
            raise CommandError("You don't have an active character.")
        char: DndCharacter = author.dnd_active_character.character
        stat: str = args[0]
        second: typing.Optional[str] = args.optional(1)
        third: typing.Optional[str] = args.optional(2)

        if third:
            extra_mod: int = int(third)
        else:
            extra_mod: int = 0

        if second:
            if second.startswith("e") or second.startswith("x"):
                proficiency_mul: float = 2.0
                proficiency_name: str = " with Expertise"
            elif second.startswith("f") or second.startswith("n") or second.startswith("c"):
                proficiency_mul: float = 1.0
                proficiency_name: str = " with Proficiency"
            elif second.startswith("h") or second == "/" or second.startswith("m"):
                proficiency_mul: float = 0.5
                proficiency_name: str = " with Half Proficiency"
            elif second.startswith("h") or second == "/" or second.startswith("m"):
                proficiency_mul: float = 0.0
                proficiency_name: str = " [i]without Proficiency[/i]"
            else:
                raise CommandError(f"Unknown proficiency type '{second}'")
            proficiency_mod: int = int(char.proficiency_bonus * proficiency_mul)
        else:
            proficiency_name: str = ""
            proficiency_mod: int = 0

        if stat.startswith("st") or stat.startswith("fo"):
            stat_mod: int = char.strength_mod
            stat_name: str = "[i]STR[/i]"
        elif stat.startswith("de"):
            stat_mod: int = char.dexterity_mod
            stat_name: str = "[i]DEX[/i]"
        elif stat.startswith("co"):
            stat_mod: int = char.constitution_mod
            stat_name: str = "[i]CON[/i]"
        elif stat.startswith("in"):
            stat_mod: int = char.intelligence_mod
            stat_name: str = "[i]INT[/i]"
        elif stat.startswith("wi") or stat.startswith("sa"):
            stat_mod: int = char.wisdom_mod
            stat_name: str = "[i]WIS[/i]"
        elif stat.startswith("ch") or stat.startswith("ca"):
            stat_mod: int = char.charisma_mod
            stat_name: str = "[i]CHA[/i]"
        else:
            raise CommandError(f"Unknown stat '{stat}'")

        total_mod = stat_mod + proficiency_mod + extra_mod

        roll = self._roll()

        result = roll + total_mod

        await data.reply(f"🎲 Rolling {stat_name}{proficiency_name}{plusformat(extra_mod, empty_if_zero=True)}:\n"
                         f"{self._roll_string}"
                         f"{plusformat(stat_mod, empty_if_zero=True)}"
                         f"{plusformat(proficiency_mod, empty_if_zero=True)}"
                         f"{plusformat(extra_mod, empty_if_zero=True)}"
                         f" = "
                         f"{roll}{plusformat(total_mod, empty_if_zero=True)}"
                         f" = "
                         f"[b]{result}[/b]")
