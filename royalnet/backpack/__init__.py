"""A Pack that is imported by default by all Royalnet instances.

Keep things here to a minimum!"""

from . import commands, tables, stars, events
from .commands import available_commands
from .tables import available_tables
from .stars import available_page_stars, available_exception_stars
from .events import available_events

__all__ = [
    "commands",
    "tables",
    "stars",
    "events",
    "available_commands",
    "available_tables",
    "available_page_stars",
    "available_exception_stars",
    "available_events",
]
