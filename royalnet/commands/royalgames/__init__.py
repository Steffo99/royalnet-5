"""Commands that can be used in bots.

These probably won't suit your needs, as they are tailored for the bots of the Royal Games gaming community, but they
 may be useful to develop new ones."""

from .ping import PingCommand
from .ciaoruozi import CiaoruoziCommand
from .color import ColorCommand
from .cv import CvCommand

__all__ = ["PingCommand",
           "CiaoruoziCommand",
           "ColorCommand",
           "CvCommand"]
