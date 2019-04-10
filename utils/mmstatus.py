import enum


class MatchmakingStatus(enum.IntEnum):
    WAIT_FOR_ME = 1
    READY = 2
    MAYBE = 3
    SOMEONE_ELSE = 4
    IGNORED = -1
