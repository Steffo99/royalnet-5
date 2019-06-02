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
    """Convert an :py:class:`int` to a :py:class:`str`, prepending a ``+`` if it's greater than 0.

    Parameters:
        i: the :py:class:`int` to convert.

    Returns:
        The resulting :py:class:`str`."""
    if i >= 0:
        return f"+{i}"
    return str(i)


def fileformat(string: str) -> str:
    """Ensure a string can be used as a filename by replacing all non-word characters with underscores.
    
    Parameters:
        string: the input string.
    
    Returns:
        A valid filename string."""
    return re.sub(r"\W", "_", string)


def ytdldateformat(string: typing.Optional[str], separator: str = "-") -> str:
    """Convert the weird date string returned by ``youtube-dl`` into the ``YYYY-MM-DD`` format.
    
    Parameters:
        string: the input string, in the ``YYYYMMDD`` format.
        separator: the string to add between the years, the months and the days. Defaults to ``-``.
        
    Returns:
        The resulting string, in the format ``YYYY-MM-DD`` format."""
    if string is None:
        return ""
    return f"{string[0:4]}{separator}{string[4:6]}{separator}{string[6:8]}"


def numberemojiformat(l: typing.List[str]) -> str:
    number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    extra_emoji = "*️⃣"
    result = ""
    for index, element in enumerate(l):
        try:
            result += f"{number_emojis[index]} {element}\n"
        except IndexError:
            result += f"{extra_emoji} {element}\n"
    return result
