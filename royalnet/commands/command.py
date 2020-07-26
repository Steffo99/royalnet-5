import abc
from typing import *
from .commandargs import CommandArgs
from .commanddata import CommandData


class Command(metaclass=abc.ABCMeta):
    name: str = NotImplemented
    """The main name of the command.
    
    Example:
        To be able to call ``/example`` on Telegram, the name should be ``"example"``."""

    aliases: List[str] = []
    """A list of possible aliases for a command.
    
    Example:
        To be able to call ``/e`` as an alias for ``/example``, one should set aliases to ``["e"]``."""

    description: str = NotImplemented
    """A small description of the command, to be displayed when the command is being autocompleted."""

    syntax: str = ""
    """The syntax of the command, to be displayed when a :py:exc:`InvalidInputError` is raised,
     in the format ``(required_arg) [optional_arg]``."""

    def __init__(self, serf, config):
        self.serf = serf
        self.config = config

    def __str__(self):
        return f"[c]{self.serf.prefix}{self.name}[/c]"

    @property
    def alchemy(self):
        """A shortcut for :attr:`.interface.alchemy`."""
        return self.serf.alchemy

    @property
    def loop(self):
        """A shortcut for :attr:`.interface.loop`."""
        return self.serf.loop

    @abc.abstractmethod
    async def run(self, args: CommandArgs, data: CommandData) -> None:
        raise NotImplementedError()
