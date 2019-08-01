import typing
from ..error import UnsupportedError
if typing.TYPE_CHECKING:
    from .call import Call
    from ..utils import NetworkHandler


class Command:
    """The base class from which all commands should inherit."""

    command_name: typing.Optional[str] = NotImplemented
    """The name of the command. To have ``/example`` on Telegram, the name should be ``example``. If the name is None or empty, the command won't be registered."""

    command_description: str = NotImplemented
    """A small description of the command, to be displayed when the command is being autocompleted."""

    command_syntax: str = NotImplemented
    """The syntax of the command, to be displayed when a :py:exc:`royalnet.error.InvalidInputError` is raised, in the format ``(required_arg) [optional_arg]``."""

    require_alchemy_tables: typing.Set = set()
    """A set of :py:class:`royalnet.database` tables, that must exist for this command to work."""

    network_handlers: typing.List[typing.Type["NetworkHandler"]] = []
    """A set of :py:class:`royalnet.utils.NetworkHandler`s that must exist for this command to work."""

    @classmethod
    async def common(cls, call: "Call"):
        raise UnsupportedError()

    @classmethod
    def network_handler_dict(cls):
        d = {}
        for network_handler in cls.network_handlers:
            d[network_handler.message_type] = network_handler
        return d
