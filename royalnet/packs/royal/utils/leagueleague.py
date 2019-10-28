from .leaguetier import LeagueTier
from .leaguerank import LeagueRank


class LeagueLeague:
    def __init__(self,
                 tier: LeagueTier = None,
                 rank: LeagueRank = None,
                 points: int = None,
                 wins: int = None,
                 losses: int = None,
                 inactive: bool = None,
                 hot_streak: bool = None,
                 fresh_blood: bool = None,
                 veteran: bool = None):
        self.tier: LeagueTier = tier  # IRON
        self.rank: LeagueRank = rank  # I
        self.points: int = points  # 40 LP
        self.wins: int = wins
        self.losses: int = losses
        self.inactive: bool = inactive
        self.hot_streak: bool = hot_streak
        self.fresh_blood: bool = fresh_blood
        self.veteran: bool = veteran

    def __str__(self):
        return f"[b]{self.tier} {self.rank}[/b] ({self.points} LP)"

    def __repr__(self):
        return f"<{self.__class__.__qualname__} {self}>"

    def __eq__(self, other):
        if isinstance(other, LeagueLeague):
            equal = True
            if other.veteran:
                equal &= self.veteran == other.veteran
            if other.fresh_blood:
                equal &= self.fresh_blood == other.fresh_blood
            if other.hot_streak:
                equal &= self.hot_streak == other.hot_streak
            if other.inactive:
                equal &= self.inactive == other.inactive
            if other.losses:
                equal &= self.losses == other.losses
            if other.wins:
                equal &= self.wins == other.wins
            if other.points:
                equal &= self.points == other.points
            if other.rank:
                equal &= self.rank == other.rank
            if other.tier:
                equal &= self.tier == other.tier
            return equal
        else:
            raise TypeError(f"Can't compare {self.__class__.__qualname__} with {other.__class__.__qualname__}")

    def __ne__(self, other):
        return not self.__eq__(other)

    def __bool__(self):
        result = True
        result &= self.veteran is not None
        result &= self.fresh_blood is not None
        result &= self.hot_streak is not None
        result &= self.inactive is not None
        result &= self.losses is not None
        result &= self.wins is not None
        result &= self.points is not None
        result &= self.rank is not None
        result &= self.tier is not None
        return result

    def __composite_values__(self):
        return self.tier, \
               self.rank, \
               self.points, \
               self.wins, \
               self.losses, \
               self.inactive, \
               self.hot_streak, \
               self.fresh_blood, \
               self.veteran

    @property
    def played(self):
        return self.wins + self.losses

    @property
    def winrate(self):
        return self.wins / self.played

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            tier=d["tier"],
            rank=d["rank"],
            points=d["leaguePoints"],
            wins=d["wins"],
            losses=d["losses"],
            inactive=d["inactive"],
            hot_streak=d["hotStreak"],
            fresh_blood=d["freshBlood"],
            veteran=d["veteran"],
        )
