# Imports go here!
from royalnet.packs.common.tables import User
from royalnet.packs.common.tables import Telegram
from royalnet.packs.common.tables import Discord

from .diario import Diario
from .aliases import Alias
from .wikipages import WikiPage
from .wikirevisions import WikiRevision
from .bios import Bio
from .reminders import Reminder
from .triviascores import TriviaScore
from .mmevents import MMEvent
from .mmresponse import MMResponse
from .leagueoflegends import LeagueOfLegends

# Enter the tables of your Pack here!
available_tables = [
    User,
    Telegram,
    Discord,
    Diario,
    Alias,
    WikiPage,
    WikiRevision,
    Bio,
    Reminder,
    TriviaScore,
    MMEvent,
    MMResponse,
    LeagueOfLegends
]

# Don't change this, it should automatically generate __all__
__all__ = [table.__class__.__qualname__ for table in available_tables]
