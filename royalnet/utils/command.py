import typing
from ..error import UnsupportedError
from ..network import Message
if typing.TYPE_CHECKING:
    from .call import Call
    from ..utils import NetworkHandler


class Command:
    """A generic command, called from any source."""

    command_name: str = NotImplemented
    command_description: str = NotImplemented
    command_syntax: str = NotImplemented

    require_alchemy_tables: typing.Set = set()

    network_handlers: typing.List[typing.Type["NetworkHandler"]] = {}

    @classmethod
    async def common(cls, call: "Call"):
        raise UnsupportedError()

    @classmethod
    def network_handler_dict(cls):
        d = {}
        for network_handler in cls.network_handlers:
            d[network_handler.message_type] = network_handler
        return d
