# Imports go here!
from .dndactivecharacters import DndActiveCharacter
from .dndcharacters import DndCharacter

# Enter the tables of your Pack here!
available_tables = [
    DndActiveCharacter,
    DndCharacter,
]

# Don't change this, it should automatically generate __all__
__all__ = [table.__class__.__qualname__ for table in available_tables]
