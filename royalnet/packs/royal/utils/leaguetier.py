import enum


class LeagueTier(enum.Enum):
    IRON = 0
    BRONZE = 1
    SILVER = 2
    GOLD = 3
    PLATINUM = 4
    DIAMOND = 5
    MASTER = 6
    GRANDMASTER = 7
    CHALLENGER = 8

    def __str__(self):
        return self.name.capitalize()

    def __repr__(self):
        return f"{self.__class__.__qualname__}.{self.name}"

    def __gt__(self, other):
        return self.value > other.value

    @classmethod
    def from_string(cls, string: str):
        return cls.__members__.get(string)
