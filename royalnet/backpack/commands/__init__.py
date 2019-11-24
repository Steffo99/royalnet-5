# Imports go here!
from .version import VersionCommand
from .exception import ExceptionCommand
from .excevent import ExceventCommand

# Enter the commands of your Pack here!
available_commands = [
    VersionCommand,
    ExceptionCommand,
    ExceventCommand,
]

# Don't change this, it should automatically generate __all__
__all__ = [command.__name__ for command in available_commands]
