# Imports go here!
from .roll import RollCommand
from .dice import DiceCommand

# Enter the commands of your Pack here!
available_commands = [
    RollCommand,
    DiceCommand,
]

# Don't change this, it should automatically generate __all__
__all__ = [command.__class__.__qualname__ for command in available_commands]
