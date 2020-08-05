# Imports go here!
from .royalnetaliases import RoyalnetaliasesCommand
from .royalnetroles import RoyalnetrolesCommand
from .royalnetsync import RoyalnetsyncCommand
from .royalnetversion import RoyalnetversionCommand

# Enter the commands of your Pack here!
available_commands = [
    RoyalnetversionCommand,
    RoyalnetsyncCommand,
    RoyalnetrolesCommand,
    RoyalnetaliasesCommand,
]

# Don't change this, it should automatically generate __all__
__all__ = [command.__name__ for command in available_commands]
