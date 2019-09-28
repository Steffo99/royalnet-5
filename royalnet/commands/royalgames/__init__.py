"""Commands that can be used in bots.

These probably won't suit your needs, as they are tailored for the bots of the User Games gaming community, but they
 may be useful to develop new ones."""

from .ciaoruozi import CiaoruoziCommand
from .color import ColorCommand
from .cv import CvCommand
from .diario import DiarioCommand
from .mp3 import Mp3Command
from .pause import PauseCommand
from .ping import PingCommand
from .play import PlayCommand
from .playmode import PlaymodeCommand
from .queue import QueueCommand
from .rage import RageCommand
from .reminder import ReminderCommand
from .ship import ShipCommand
from .skip import SkipCommand
from .smecds import SmecdsCommand
from .summon import SummonCommand
from .videochannel import VideochannelCommand
from .dnditem import DnditemCommand
from .dndspell import DndspellCommand
from .trivia import TriviaCommand
from .mm import MmCommand
from .zawarudo import ZawarudoCommand


commands = [
    CiaoruoziCommand,
    ColorCommand,
    CvCommand,
    DiarioCommand,
    Mp3Command,
    PauseCommand,
    PingCommand,
    PlayCommand,
    PlaymodeCommand,
    QueueCommand,
    RageCommand,
    ReminderCommand,
    ShipCommand,
    SkipCommand,
    SmecdsCommand,
    SummonCommand,
    VideochannelCommand,
    DnditemCommand,
    DndspellCommand,
    TriviaCommand,
    MmCommand,
    ZawarudoCommand
]


__all__ = [command.__name__ for command in commands]
