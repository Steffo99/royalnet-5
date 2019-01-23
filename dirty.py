class Dirty:
    def __init__(self, initial_value):
        self.initial_value = initial_value
        self.value = initial_value

    def is_clean(self):
        return self.initial_value == self.value

    def is_dirty(self):
        return not self.is_clean()

    def __bool__(self):
        return self.is_dirty()


class DirtyDelta(Dirty):
    @property
    def delta(self):
        return self.value - self.initial_value

    @delta.setter
    def delta(self, value):
        self.value = self.initial_value + value
