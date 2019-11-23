# Imports go here!
from .summon import SummonEvent
from .play import PlayEvent

# Enter the commands of your Pack here!
available_events = [
    SummonEvent,
    PlayEvent,
]

# Don't change this, it should automatically generate __all__
__all__ = [command.__name__ for command in available_events]
