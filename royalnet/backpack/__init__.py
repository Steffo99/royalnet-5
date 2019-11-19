"""A Pack that is imported by default by all :mod:`royalnet` instances."""

from . import commands, tables, stars
from .commands import available_commands
from .tables import available_tables
from .stars import available_page_stars, available_exception_stars

__all__ = [
    "commands",
    "tables",
    "stars",
    "available_commands",
    "available_tables",
    "available_page_stars",
    "available_exception_stars",
]
