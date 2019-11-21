"""A :class:`Serf` implementation for Discord.

It is pretty unstable, compared to the rest of the bot, but it *should* work."""

from .createrichembed import create_rich_embed
from .escape import escape
from .discordserf import DiscordSerf
from . import discordbard

__all__ = [
    "create_rich_embed",
    "escape",
    "DiscordSerf",
    "discordbard",
]
