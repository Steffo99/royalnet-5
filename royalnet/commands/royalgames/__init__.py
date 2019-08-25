"""Commands that can be used in bots.

These probably won't suit your needs, as they are tailored for the bots of the Royal Games gaming community, but they
 may be useful to develop new ones."""

from .ping import PingCommand
from .ciaoruozi import CiaoruoziCommand
from .color import ColorCommand
from .cv import CvCommand
from .diario import DiarioCommand
from .mp3 import Mp3Command
from .summon import SummonCommand
from .pause import PauseCommand
from .play import PlayCommand
from .playmode import PlaymodeCommand
from .queue import QueueCommand
from .reminder import ReminderCommand

__all__ = ["PingCommand",
           "CiaoruoziCommand",
           "ColorCommand",
           "CvCommand",
           "DiarioCommand",
           "Mp3Command",
           "SummonCommand",
           "PauseCommand",
           "PlayCommand",
           "PlaymodeCommand",
           "QueueCommand",
           "ReminderCommand"]
