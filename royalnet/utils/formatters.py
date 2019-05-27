import typing
import re


def andformat(l: typing.List[str], middle=", ", final=" and ") -> str:
    """Convert a :py:class:`list` to a :py:class:`str` by adding ``final`` between the last two elements and ``middle`` between the others.

    Parameters:
        l: the input :py:class:`list`.
        middle: the :py:class:`str` to be added between the middle elements.
        final: the :py:class:`str` to be added between the last two elements.

    Returns:
        The resulting :py:class:`str`."""
    result = ""
    for index, item in enumerate(l):
        result += item
        if index == len(l) - 2:
            result += final
        elif index != len(l) - 1:
            result += middle
    return result


def plusformat(i: int) -> str:
    """Convert an :py:class:`int` to a :py:class:`str`, adding a ``+`` if they are greater than 0.

    Parameters:
        i: the :py:class:`int` to convert.

    Returns:
        The resulting :py:class:`str`."""
    if i >= 0:
        return f"+{i}"
    return str(i)


def fileformat(string: str) -> str:
    """Ensure a string can be used as a filename by replacing all non-word characters with underscores."""
    return re.sub(r"\W", "_", string)


def ytdldateformat(string: typing.Optional[str], separator: str = "-") -> str:
    if string is None:
        return ""
    return f"{string[0:4]}-{string[4:6]}-{string[6:8]}"
