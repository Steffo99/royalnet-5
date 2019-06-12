import typing
from ..error import UnsupportedError
if typing.TYPE_CHECKING:
    from .call import Call
    from ..utils import NetworkHandler


class Command:
    """The base class from which all commands should inherit.
    
    Attributes:
        command_name: The name of the command. To have ``/example`` on Telegram, the name should be ``example``.
        command_description: A small description of the command, to be displayed when the command is being autocompleted.
        command_syntax: The syntax of the command, to be displayed when a :py:exc:`royalnet.error.InvalidInputError` is raised, in the format ``(required_arg) [optional_arg]``.
        require_alchemy_tables: A set of :py:class:`royalnet.database` tables, that must exist for this command to work.
        network_handlers: A list of :py:class:`royalnet.utils.NetworkHandler`s that must exist for this command to work."""

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
