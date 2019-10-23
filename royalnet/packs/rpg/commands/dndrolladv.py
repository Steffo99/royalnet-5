import typing
import random
from royalnet.commands import *
from royalnet.utils import plusformat
from .dndroll import DndrollCommand
from ..tables import DndCharacter, DndActiveCharacter


class DndrolladvCommand(DndrollCommand):
    name: str = "dndrolladv"

    description: str = "Roll with advantage as the active DnD character."

    aliases = ["dra", "dndra", "drolladv"]

    syntax = "{stat} [proficiency] [modifier]"

    tables = {DndCharacter, DndActiveCharacter}

    @staticmethod
    def _roll():
        first = random.randrange(1, 21)
        second = random.randrange(1, 21)
        return max(first, second)

    _roll_string = "2d20h1"
