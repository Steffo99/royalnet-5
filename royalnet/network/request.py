from .data import Data


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
