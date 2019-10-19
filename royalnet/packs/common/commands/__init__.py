# Imports go here!
from .ping import PingCommand
from .version import VersionCommand

# Enter the commands of your Pack here!
available_commands = [
    PingCommand,
    VersionCommand
]

# Don't change this, it should automatically generate __all__
__all__ = [command.__class__.__qualname__ for command in available_commands]
