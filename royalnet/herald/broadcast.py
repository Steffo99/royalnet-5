from typing import *


class Broadcast:
    def __init__(self, handler: str, data: dict, msg_type: Optional[str] = None):
        super().__init__()
        if msg_type is not None:
            assert msg_type == self.__class__.__name__
        self.msg_type = self.__class__.__name__
        self.handler: str = handler
        self.data: dict = data

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.handler == other.handler and self.data == other.data
        return False

    def __repr__(self):
        return f"{self.__class__.__qualname__}(handler={self.handler}, data={self.data})"
