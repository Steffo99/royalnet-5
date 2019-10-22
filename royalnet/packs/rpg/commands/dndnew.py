import re
from royalnet.commands import *
from ..tables import DndCharacter


class DndnewCommand(Command):
    name: str = "dndnew"

    description: str = "Create a new DnD character."

    aliases = ["dn", "dndn", "new", "dnew"]

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

    tables = {DndCharacter}

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        name, level, strength, dexterity, constitution, intelligence, wisdom, charisma, max_hp, armor_class = \
            args.match(r"([\w ]+\w)\s*"
                       r"LV\s+(\d+)\s+"
                       r"STR\s+(\d+)\s+"
                       r"DEX\s+(\d+)\s+"
                       r"COS\s+(\d+)\s+"
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
        char = self.alchemy.DndCharacter(name=name,
                                         level=level,
                                         strength=strength,
                                         dexterity=dexterity,
                                         constitution=constitution,
                                         intelligence=intelligence,
                                         wisdom=wisdom,
                                         charisma=charisma,
                                         max_hp=max_hp,
                                         armor_class=armor_class,
                                         creator=author)
        data.session.add(char)
        await data.session_commit()
        await data.reply(f"✅ Character [b]{char.name}[/b] ([c]{char.character_id}[/c]) was created!")
