from royalnet.commands import *
from royalnet.utils import asyncify
from ..tables import DndCharacter, DndActiveCharacter


class DndinfoCommand(Command):
    name: str = "dndinfo"

    description: str = "Display the character sheet of the active DnD character."

    aliases = ["di", "dndi", "info", "dinfo"]

    tables = {DndCharacter, DndActiveCharacter}

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        author = await data.get_author(error_if_none=True)
        if author.dnd_active_character is None:
            raise CommandError("You don't have an active character.")
        await data.reply(author.dnd_active_character.character.character_sheet())
