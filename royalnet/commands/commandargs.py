import re
import typing
from .errors import InvalidInputError


class CommandArgs(list):
    """An interface to easily access the arguments of a command.

    Inherits from :class:`list`."""

    def __getitem__(self, item):
        """Access arguments as if they were a :class:`list`.

        Raises:
            InvalidInputError: if the requested argument does not exist.

        Examples:
            ::

                # /pasta spaghetti aldente
                >>> self[0]
                "spaghetti"
                >>> self[1]
                "aldente"
                >>> self[2]
                # InvalidInputError: Missing argument #3.
                >>> self[0:2]
                ["spaghetti", "aldente"]

        """
        if isinstance(item, int):
            try:
                return super().__getitem__(item)
            except IndexError:
                raise InvalidInputError(f'Missing argument #{item+1}.')
        if isinstance(item, slice):
            try:
                return super().__getitem__(item)
            except IndexError:
                raise InvalidInputError(f'Cannot get arguments from #{item.start+1} to #{item.stop+1}.')
        raise ValueError(f"Invalid type passed to CommandArgs.__getattr__: {type(item)}")

    def joined(self, *, require_at_least=0) -> str:
        """Get the arguments as a space-joined string.

        Parameters:
            require_at_least: the minimum amount of arguments required.

        Raises:
            InvalidInputError: if there are less than ``require_at_least`` arguments.

        Returns:
            The space-joined string.

        Examples:
            ::

                # /pasta spaghetti aldente
                >>> self.joined()
                "spaghetti aldente"
                >>> self.joined(require_at_least=3)
                # InvalidInputError: Not enough arguments specified (minimum is 3).

            """
        if len(self) < require_at_least:
            raise InvalidInputError(f"Not enough arguments specified (minimum is {require_at_least}).")
        return " ".join(self)

    def match(self, pattern: typing.Union[str, typing.Pattern], *flags) -> typing.Sequence[typing.AnyStr]:
        """Match the :meth:`.joined` string to a :class:`re.Pattern`-like object.

        Parameters:
            pattern: The regex pattern to be passed to :func:`re.match`.

        Raises:
            InvalidInputError: if the pattern doesn't match.

        Returns:
            The matched groups, as returned by :func:`re.Match.groups`."""
        text = self.joined()
        match = re.match(pattern, text, *flags)
        if match is None:
            raise InvalidInputError("Invalid syntax.")
        return match.groups()

    def optional(self, index: int, default=None) -> typing.Optional[str]:
        """Get the argument at a specific index, but don't raise an error if nothing is found, instead returning the
        ``default`` value.

        Parameters:
            index: The index of the argument you want to retrieve.
            default: The value returned if the argument is missing.

        Returns:
            Either the argument or the ``default`` value, defaulting to ``None``.

        Examples:
            ::

                # /pasta spaghetti aldente
                >>> self.optional(0)
                "spaghetti"
                >>> self.optional(2)
                None
                >>> self.optional(2, default="carbonara")
                "carbonara"

        """
        try:
            return self[index]
        except InvalidInputError:
            return default
