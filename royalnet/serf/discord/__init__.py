"""A :class:`Serf` implementation for Discord.

It requires (obviously) the ``discord`` extra to be installed.

Install it with: ::

    pip install royalnet[discord]

"""

from .escape import escape
from .discordserf import DiscordSerf
from .playable import Playable
from .voiceplayer import VoicePlayer

__all__ = [
    "escape",
    "DiscordSerf",
    "Playable",
    "VoicePlayer",
]
