import enum


class LeagueRank(enum.Enum):
    I = 1
    II = 2
    III = 3
    IV = 4

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"{self.__class__.__qualname__}.{self.name}"

    def __gt__(self, other):
        return self.value < other.value

    @classmethod
    def from_string(cls, string: str):
        return cls.__members__.get(string)
