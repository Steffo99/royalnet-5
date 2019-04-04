import typing
if typing.TYPE_CHECKING:
    from .call import Call


class UnsupportedError(Exception):
    """The command is not supported for the specified source."""
    pass


class InvalidInputError(Exception):
    """The command has received invalid input and cannot complete."""
    pass


class CommandArgs(list):
    """The arguments of a command. Raises InvalidInputError if the requested argument does not exist."""

    def __getitem__(self, item):
        if isinstance(item, int):
            try:
                return super().__getitem__(item)
            except IndexError:
                raise InvalidInputError(f'Tried to get missing [{item}] arg from CommandArgs')
        if isinstance(item, slice):
            try:
                return super().__getitem__(item)
            except IndexError:
                raise InvalidInputError(f'Tried to get invalid [{item}] slice from CommandArgs')
        raise ValueError(f"Invalid type passed to CommandArgs.__getattr__: {type(item)}")


class Command:
    """A generic command, called from any source."""

    command_name: str = NotImplemented
    command_title: str = NotImplemented
    command_syntax: str = NotImplemented

    require_alchemy_tables: typing.Set = set()

    async def common(self, call: "Call"):
        raise NotImplementedError()
