import typing
if typing.TYPE_CHECKING:
    from .call import Call


class UnsupportedError(Exception):
    """The command is not supported for the specified source."""
    pass


class InvalidInputError(Exception):
    """The command has received invalid input and cannot complete."""
    pass


class CommandArgs:
    """The arguments of a command. Raises InvalidInputError if the requested argument does not exist."""
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __getitem__(self, item):
        if isinstance(item, int):
            try:
                return self.args[item]
            except IndexError:
                raise InvalidInputError(f'Tried to get missing [{item}] arg from CommandArgs')
        elif isinstance(item, str):
            try:
                return self.kwargs[item]
            except IndexError:
                raise InvalidInputError(f'Tried to get missing ["{item}"] kwarg from CommandArgs')
        raise ValueError(f"Invalid type passed to CommandArgs.__getattr__: {type(item)}")


class Command:
    """A generic command, called from any source."""

    command_name: str = NotImplemented
    command_title: str = NotImplemented

    require_alchemy_tables: typing.Set = set()

    async def common(self, call: "Call", args: CommandArgs):
        raise NotImplementedError()
