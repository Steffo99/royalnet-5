"""Commands that can be used in bots. 

These probably won't suit your needs, as they are tailored for the bots of the Royal Games gaming community, but they may be useful to develop new ones."""

from .null import NullCommand
from .ping import PingCommand
from .ship import ShipCommand
from .smecds import SmecdsCommand
from .ciaoruozi import CiaoruoziCommand
from .color import ColorCommand
from .sync import SyncCommand
from .diario import DiarioCommand
from .rage import RageCommand
from .dateparser import DateparserCommand
from .author import AuthorCommand
from .reminder import ReminderCommand
from .kvactive import KvactiveCommand
from .kv import KvCommand
from .kvroll import KvrollCommand
from .videoinfo import VideoinfoCommand
from .summon import SummonCommand
from .play import PlayCommand
from .skip import SkipCommand
from .playmode import PlaymodeCommand
from .videochannel import VideochannelCommand
from .missing import MissingCommand
from .cv import CvCommand
from .pause import PauseCommand
from .queue import QueueCommand
from .royalnetprofile import RoyalnetprofileCommand


__all__ = ["NullCommand", "PingCommand", "ShipCommand", "SmecdsCommand", "CiaoruoziCommand", "ColorCommand",
           "SyncCommand", "DiarioCommand", "RageCommand", "DateparserCommand", "AuthorCommand", "ReminderCommand",
           "KvactiveCommand", "KvCommand", "KvrollCommand", "VideoinfoCommand", "SummonCommand", "PlayCommand",
           "SkipCommand", "PlaymodeCommand", "VideochannelCommand", "MissingCommand", "CvCommand", "PauseCommand",
           "QueueCommand", "RoyalnetprofileCommand"]
