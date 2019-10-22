import typing
from .commandinterface import CommandInterface
from .commandargs import CommandArgs
from .commanddata import CommandData


class Command:
    name: str = NotImplemented
    """The main name of the command.
     To have ``/example`` on Telegram, the name should be ``example``."""

    aliases: typing.List[str] = []
    """A list of possible aliases for a command.
    To have ``/e`` as alias for ``/example``, one should set aliases to ``["e"]``."""

    description: str = NotImplemented
    """A small description of the command, to be displayed when the command is being autocompleted."""

    syntax: str = ""
    """The syntax of the command, to be displayed when a :py:exc:`royalnet.error.InvalidInputError` is raised,
     in the format ``(required_arg) [optional_arg]``."""

    tables: typing.Set = set()
    """A set of :py:class:`royalnet.database` tables that must exist for this command to work."""

    def __init__(self, interface: CommandInterface):
        self.interface = interface

    @property
    def alchemy(self):
        """A shortcut to ``self.interface.alchemy``"""
        return self.interface.alchemy

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        raise NotImplementedError()
