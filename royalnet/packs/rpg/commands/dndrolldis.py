import typing
import random
from royalnet.commands import *
from royalnet.utils import plusformat
from .dndroll import DndrollCommand
from ..tables import DndCharacter, DndActiveCharacter


class DndrolldisCommand(DndrollCommand):
    name: str = "dndrolldis"

    description: str = "Roll with disadvantage as the active DnD character."

    aliases = ["drd", "dndrd", "drolldis"]

    syntax = "{stat} [proficiency] [modifier]"

    tables = {DndCharacter, DndActiveCharacter}

    @staticmethod
    def _roll():
        first = random.randrange(1, 21)
        second = random.randrange(1, 21)
        return min(first, second)

    _roll_string = "2d20l1"
