from royalnet.commands import *
from royalnet.utils import asyncify
from ..tables import DndCharacter, DndActiveCharacter


class DndactiveCommand(Command):
    name: str = "dndactive"

    description: str = "Set a DnD character as active."

    aliases = ["da", "dnda", "active", "dactive"]

    syntax = "{name|id}"

    tables = {DndCharacter, DndActiveCharacter}

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        identifier = args.optional(0)
        author = await data.get_author(error_if_none=True)
        if identifier is None:
            # Display the active character
            if author.dnd_active_character is None:
                await data.reply("ℹ️ You have no active characters.")
            else:
                await data.reply(f"ℹ️ You currently active character is [b]{author.dnd_active_character}[/b].")
            return
        try:
            identifier = int(identifier)
        except ValueError:
            # Find the character by name
            chars = await asyncify(data.session.query(self.alchemy.DndCharacter).filter_by(name=identifier).all)
            if len(chars) >= 2:
                char_string = "\n".join([f"[c]{char.character_id}[/c] (LV {char.level}) by {char.creator})" for char in chars])
                raise CommandError(f"Multiple characters share the name {identifier}, "
                                   f"please activate them using their id:\n{char_string}")
            elif len(chars) == 1:
                char = chars[0]
            else:
                char = None
        else:
            # Find the character by id
            char = await asyncify(data.session.query(self.alchemy.DndCharacter)
                                              .filter_by(character_id=identifier)
                                              .one_or_none)
        if char is None:
            raise CommandError("No character found.")
        # Check if the player already has an active character
        if author.dnd_active_character is None:
            # Create a new active character
            achar = self.alchemy.DndActiveCharacter(character=char, user=author)
            data.session.add(achar)
        else:
            # Change the active character
            author.dnd_active_character.character = char
        await data.session_commit()
        await data.reply(f"✅ Active character set to [b]{char}[/b]!")
