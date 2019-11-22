"""A :class:`Serf` implementation for Discord.

It is pretty unstable, compared to the rest of the bot, but it *should* work."""

from .escape import escape
from .discordserf import DiscordSerf
from . import discordbard

__all__ = [
    "escape",
    "DiscordSerf",
    "discordbard",
]
