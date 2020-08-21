# Imports go here!
from .aliases import Alias
from .discord import Discord
from .roles import Role
from .telegram import Telegram
from .tokens import Token
from .users import User

# Enter the tables of your Pack here!
available_tables = {
    User,
    Telegram,
    Discord,
    Alias,
    Token,
    Role,
}

# Don't change this, it should automatically generate __all__
__all__ = [table.__name__ for table in available_tables]
