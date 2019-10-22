from royalnet.commands import *
from ..tables import DndCharacter


class DndnewCommand(Command):
    name: str = "dndnew"

    description: str = "Create a new D&D character."

    aliases = ["dn", "dndn", "new"]

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
             "MAXHP {maxhp}\n" \
             "AC {armorclass}"

    tables = {}

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        name = args[0]
        ...