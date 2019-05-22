class Data:
    """Royalnet data. All fields in this class will be converted to a dict when about to be sent."""
    def __init__(self):
        pass

    def to_dict(self):
        return self.__dict__


class Request(Data):
    """A Royalnet request. It contains the name of the requested handler, in addition to the data."""

    def __init__(self, handler: str, data: dict):
        super().__init__()
        self.handler: str = handler
        self.data: dict = data

    @staticmethod
    def from_dict(d: dict):
        return Request(**d)

    def __eq__(self, other):
        if isinstance(other, Request):
            return self.handler == other.handler and self.data == other.data
        return False
