# Imports go here!
from .users import User
from .telegram import Telegram
from .discord import Discord

# Enter the tables of your Pack here!
available_tables = [
    User,
    Telegram,
    Discord
]

# Don't change this, it should automatically generate __all__
__all__ = [table.__class__.__qualname__ for table in available_tables]
