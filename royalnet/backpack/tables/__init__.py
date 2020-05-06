# Imports go here!
from .users import User
from .telegram import Telegram
from .discord import Discord
from .matrix import Matrix
from .aliases import Alias
from .tokens import Token
from .roles import Role

# Enter the tables of your Pack here!
available_tables = {
    User,
    Telegram,
    Discord,
    Matrix,
    Alias,
    Token,
    Role,
}

# Don't change this, it should automatically generate __all__
__all__ = [table.__name__ for table in available_tables]
