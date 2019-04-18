from ..network import Message
from ..error import UnsupportedError


class NetworkHandler:
    """The NetworkHandler functions are called when a specific Message type is received."""

    message_type = NotImplemented

    def __getattribute__(self, item: str):
        try:
            return self.__dict__[item]
        except KeyError:
            raise UnsupportedError()
