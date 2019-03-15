import re
from ..utils import Command, Call


SHIP_RESULT = "💕 {one} + {two} = <b>{result}</b>"


class ShipCommand(Command):

    command_name = "ship"
    command_title = "Create a ship between two items"

    async def common(self, call: Call, *args, **kwargs):
        name_one = args[0]
        name_two = args[1]
        if name_two == "+":
            name_two = args[2]
        name_one = name_one.lower()
        name_two = name_two.lower()
        match_one = re.search(r"^[A-Za-z][^aeiouAEIOU]*[aeiouAEIOU]?", name_one)
        if match_one is None:
            part_one = name_one[:int(len(name_one) / 2)]
        else:
            part_one = match_one.group(0)
        match_two = re.search(r"[^aeiouAEIOU]*[aeiouAEIOU]?[A-Za-z]$", name_two)
        if match_two is None:
            part_two = name_two[int(len(name_two) / 2):]
        else:
            part_two = match_two.group(0)
        mixed = part_one + part_two  # TODO: find out what exceptions this could possibly raise
        await call.reply(SHIP_RESULT.format(one=name_one.capitalize(),
                                            two=name_two.capitalize(),
                                            result=mixed.capitalize()))
