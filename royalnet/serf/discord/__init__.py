"""A :class:`Serf` implementation for Discord.

It requires (obviously) the ``discord`` extra to be installed.

Install it with: ::

    pip install royalnet[discord]

"""

from .discordserf import DiscordSerf
from .escape import escape

__all__ = [
    "escape",
    "DiscordSerf",
]
