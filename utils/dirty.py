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
    def difference(self):
        if self.initial_value is None:
            initial_value = 0
        else:
            initial_value = self.initial_value
        if self.value is None:
            value = 0
        else:
            value = self.value
        return value - initial_value

    @property
    def delta(self):
        return abs(self.difference)

    def difference_string(self):
        if self.difference > 0:
            return f"+{self.difference}"
        return self.difference
