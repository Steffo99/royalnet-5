from ..network import Message
from ..error import UnsupportedError


class NetworkHandler:
    """The NetworkHandler functions are called when a specific Message type is received."""

    message_type = NotImplemented
