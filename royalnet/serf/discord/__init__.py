"""A :class:`Serf` implementation for Discord.

It is pretty unstable, compared to the rest of the bot, but it *should* work."""

from .escape import escape
from .discordserf import DiscordSerf
from .playable import Playable
from .playableytdqueue import PlayableYTDQueue
from .voiceplayer import VoicePlayer

__all__ = [
    "escape",
    "DiscordSerf",
    "Playable",
    "PlayableYTDQueue",
    "VoicePlayer",
]
