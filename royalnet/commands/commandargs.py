import re
import typing
from royalnet.error import InvalidInputError


class CommandArgs(list):
    """An interface to access the arguments of a command with ease."""

    def __getitem__(self, item):
        """Arguments can be accessed with an array notation, such as ``args[0]``.

        Raises:
            royalnet.error.InvalidInputError: if the requested argument does not exist."""
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

    def joined(self, *, require_at_least=0) -> str:
        """Get the arguments as a space-joined string.

        Parameters:
            require_at_least: the minimum amount of arguments required, will raise :py:exc:`royalnet.error.InvalidInputError` if the requirement is not fullfilled.

        Raises:
            royalnet.error.InvalidInputError: if there are less than ``require_at_least`` arguments.

        Returns:
            The space-joined string."""
        if len(self) < require_at_least:
            raise InvalidInputError("Not enough arguments")
        return " ".join(self)

    def match(self, pattern: typing.Pattern) -> typing.Sequence[typing.AnyStr]:
        """Match the :py:func:`royalnet.utils.commandargs.joined` to a regex pattern.

        Parameters:
            pattern: The regex pattern to be passed to :py:func:`re.match`.

        Raises:
            royalnet.error.InvalidInputError: if the pattern doesn't match.

        Returns:
            The matched groups, as returned by :py:func:`re.Match.groups`."""
        text = self.joined()
        match = re.match(pattern, text)
        if match is None:
            raise InvalidInputError("Pattern didn't match")
        return match.groups()

    def optional(self, index: int, default=None):
        """Get the argument at a specific index, but don't raise an error if nothing is found, instead returning the ``default`` value.

        Parameters:
            index: The index of the argument you want to retrieve.
            default: The value returned if the argument is missing.

        Returns:
            Either the argument or the ``default`` value, defaulting to ``None``."""
        try:
            return self[index]
        except InvalidInputError:
            return default
