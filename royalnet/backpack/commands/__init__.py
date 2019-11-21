# Imports go here!
from .ping import PingCommand
from .version import VersionCommand
from .summon import SummonCommand
from .play import PlayCommand

# Enter the commands of your Pack here!
available_commands = [
    PingCommand,
    VersionCommand,
    SummonCommand,
    PlayCommand,
]

# Don't change this, it should automatically generate __all__
__all__ = [command.__name__ for command in available_commands]
