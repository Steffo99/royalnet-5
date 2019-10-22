import re
from royalnet.commands import *
from ..tables import DndCharacter, DndActiveCharacter


class DndeditCommand(Command):
    name: str = "dndedit"

    description: str = "Edit the active DnD character."

    aliases = ["de", "dnde", "edit", "dedit"]

    syntax = "{name}\n" \
             "LV {level}\n" \
             "\n" \
             "STR {strength}\n" \
             "DEX {dexterity}\n" \
             "CON {constitution}\n" \
             "INT {intelligence}\n" \
             "WIS {wisdom}\n" \
             "CHA {charisma}\n" \
             "\n" \
             "MAXHP {max_hp}\n" \
             "AC {armor_class}"

    tables = {DndCharacter, DndActiveCharacter}

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        name, level, strength, dexterity, constitution, intelligence, wisdom, charisma, max_hp, armor_class = \
            args.match(r"([\w ]+\w)\s*"
                       r"LV\s+(\d+)\s+"
                       r"STR\s+(\d+)\s+"
                       r"DEX\s+(\d+)\s+"
                       r"CON\s+(\d+)\s+"
                       r"INT\s+(\d+)\s+"
                       r"WIS\s+(\d+)\s+"
                       r"CHA\s+(\d+)\s+"
                       r"MAXHP\s+(\d+)\s+"
                       r"AC\s+(\d+)", re.IGNORECASE)
        try:
            int(name)
        except ValueError:
            pass
        else:
            raise CommandError("Character names cannot be composed of only a number.")
        author = await data.get_author(error_if_none=True)
        char = author.dnd_active_character.character
        char.name = name
        char.level = level
        char.strength = strength
        char.dexterity = dexterity
        char.constitution = constitution
        char.intelligence = intelligence
        char.wisdom = wisdom
        char.charisma = charisma
        char.max_hp = max_hp
        char.armor_class = armor_class
        data.session.add(char)
        await data.session_commit()
        await data.reply(f"✅ Edit successful!")
