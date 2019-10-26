import typing
import re
from royalnet.commands import *
from royalnet.utils import safeformat


class ShipCommand(Command):
    name: str = "ship"

    aliases = ["⛵️"]

    description: str = "Crea una ship tra due nomi."

    syntax = "{nomeuno} {nomedue}"

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        name_one = args[0]
        name_two = args[1]
        if name_two == "+":
            name_two = args[2]
        name_one = name_one.lower()
        name_two = name_two.lower()
        # Get all letters until the first vowel, included
        match_one = re.search(r"^[A-Za-z][^aeiouAEIOU]*[aeiouAEIOU]?", name_one)
        if match_one is None:
            part_one = name_one[:int(len(name_one) / 2)]
        else:
            part_one = match_one.group(0)
        # Get all letters from the second to last vowel, excluded
        match_two = re.search(r"[^aeiouAEIOU]*[aeiouAEIOU]?[A-Za-z]$", name_two)
        if match_two is None:
            part_two = name_two[int(len(name_two) / 2):]
        else:
            part_two = match_two.group(0)
        # Combine the two name parts
        mixed = part_one + part_two
        await data.reply(safeformat("💕 {one} + {two} = [b]{result}[/b]",
                                    one=name_one.capitalize(),
                                    two=name_two.capitalize(),
                                    result=mixed.capitalize()))
