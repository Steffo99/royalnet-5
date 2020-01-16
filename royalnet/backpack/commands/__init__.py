# Imports go here!
from .version import VersionCommand
from .exception import ExceptionCommand
from .excevent import ExceventCommand
from .keyboardtest import KeyboardtestCommand

# Enter the commands of your Pack here!
available_commands = [
    VersionCommand,
]

# noinspection PyUnreachableCode
if __debug__:
    available_commands = [
        *available_commands,
        ExceptionCommand,
        ExceventCommand,
        KeyboardtestCommand,
    ]

# Don't change this, it should automatically generate __all__
__all__ = [command.__name__ for command in available_commands]
