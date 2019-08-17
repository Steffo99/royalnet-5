import typing
from ..error import UnsupportedError
from .commandinterface import CommandInterface


class Command:
    name: str = NotImplemented
    """The main name of the command.
     To have ``/example`` on Telegram, the name should be ``example``."""

    description: str = NotImplemented
    """A small description of the command, to be displayed when the command is being autocompleted."""

    syntax: str = NotImplemented
    """The syntax of the command, to be displayed when a :py:exc:`royalnet.error.InvalidInputError` is raised,
     in the format ``(required_arg) [optional_arg]``."""

    require_alchemy_tables: typing.Set = set()
    """A set of :py:class:`royalnet.database` tables that must exist for this command to work."""

    def __init__(self, interface: CommandInterface):
        self.interface = interface

    async def common(self) -> None:
        raise UnsupportedError(f"Command {self.name} can't be called on {self.interface.name}.")

    def __getattr__(self, item) -> typing.Callable:
        return self.common
