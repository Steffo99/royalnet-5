"""Commands that can be used in bots.

These probably won't suit your needs, as they are tailored for the bots of the User Games gaming community, but they
 may be useful to develop new ones."""

from .ciaoruozi import CiaoruoziCommand
from .color import ColorCommand
from .cv import CvCommand
from .diario import DiarioCommand
from .ping import PingCommand
from .rage import RageCommand
from .reminder import ReminderCommand
from .ship import ShipCommand
from .smecds import SmecdsCommand
from .videochannel import VideochannelCommand
from .dnditem import DnditemCommand
from .dndspell import DndspellCommand
from .trivia import TriviaCommand
from .mm import MmCommand


commands = [
    CiaoruoziCommand,
    ColorCommand,
    CvCommand,
    DiarioCommand,
    PingCommand,
    RageCommand,
    ReminderCommand,
    ShipCommand,
    SmecdsCommand,
    VideochannelCommand,
    DnditemCommand,
    DndspellCommand,
    TriviaCommand,
    MmCommand,
]


__all__ = [command.__name__ for command in commands]
