"""A :class:`Serf` implementation for Telegram.

It requires (obviously) the ``telegram`` extra to be installed.

Install it with: ::

    pip install royalnet[telegram]

"""

from .escape import escape
from .telegramserf import TelegramSerf

__all__ = [
    "escape",
    "TelegramSerf"
]
