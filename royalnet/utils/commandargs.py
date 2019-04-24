import re
import typing
from royalnet.error import InvalidInputError


class CommandArgs(list):
    """The arguments of a command. Raises :py:exc:`InvalidInputError` if the requested argument does not exist."""

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

    def joined(self, *, require_at_least=0):
        if len(self) < require_at_least:
            raise InvalidInputError("Not enough arguments")
        return " ".join(self)

    def match(self, pattern: typing.Pattern) -> typing.Sequence[typing.AnyStr]:
        text = self.joined()
        match = re.match(pattern, text)
        if match is None:
            raise InvalidInputError("Pattern didn't match")
        return match.groups()

    def optional(self, index: int, default=None) -> typing.Optional:
        try:
            return self[index]
        except InvalidInputError:
            return default
