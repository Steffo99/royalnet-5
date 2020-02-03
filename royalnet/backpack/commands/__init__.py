# Imports go here!
from .version import VersionCommand

# Enter the commands of your Pack here!
available_commands = [
    VersionCommand,
]

# Don't change this, it should automatically generate __all__
__all__ = [command.__name__ for command in available_commands]
