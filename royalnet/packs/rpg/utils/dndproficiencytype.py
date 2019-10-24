import enum


class DndProficiencyType(enum.Enum):
    NONE = 0
    HALF_PROFICIENCY = 0.5
    FULL_PROFICIENCY = 1
    EXPERTISE = 2

    def __str__(self):
        return str(self.value)