class Request:
    """A request sent from a :py:class:`royalnet.network.RoyalnetLink` to another.

     It contains the name of the requested handler, in addition to the data."""

    def __init__(self, handler: str, data: dict):
        super().__init__()
        self.handler: str = handler
        self.data: dict = data

    def to_dict(self):
        return self.__dict__

    @staticmethod
    def from_dict(d: dict):
        return Request(**d)

    def __eq__(self, other):
        if isinstance(other, Request):
            return self.handler == other.handler and self.data == other.data
        return False

    def __repr__(self):
        return f"royalnet.network.Request(handler={self.handler}, data={self.data})"
