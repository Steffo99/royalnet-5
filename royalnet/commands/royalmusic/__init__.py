"""Commands that can be used in bots.

These probably won't suit your needs, as they are tailored for the bots of the User Games gaming community, but they
 may be useful to develop new ones."""

from .pause import PauseCommand
from .play import PlayCommand
from .playmode import PlaymodeCommand
from .queue import QueueCommand
from .skip import SkipCommand
from .summon import SummonCommand
from .youtube import YoutubeCommand
from .soundcloud import SoundcloudCommand
from .zawarudo import ZawarudoCommand


commands = [
    PauseCommand,
    PlayCommand,
    PlaymodeCommand,
    QueueCommand,
    SkipCommand,
    SummonCommand,
    YoutubeCommand,
    SoundcloudCommand,
    ZawarudoCommand
]


__all__ = [command.__name__ for command in commands]
