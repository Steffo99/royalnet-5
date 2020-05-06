# Imports go here!
from .royalnetversion import RoyalnetversionCommand
from .royalnetsync import RoyalnetsyncCommand
from .royalnetroles import RoyalnetrolesCommand
from .royalnetaliases import RoyalnetaliasesCommand

# Enter the commands of your Pack here!
available_commands = [
    RoyalnetversionCommand,
    RoyalnetsyncCommand,
    RoyalnetrolesCommand,
    RoyalnetaliasesCommand,
]

# Don't change this, it should automatically generate __all__
__all__ = [command.__name__ for command in available_commands]
