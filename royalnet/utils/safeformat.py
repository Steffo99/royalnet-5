class SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def safeformat(string: str, **words: str) -> str:
    """:py:func:`str.format` something, but ignore missing keys instead of raising an error.

    Parameters:
        string: The base string to be formatted.
        words: The words to format the string with.

    Returns:
        The formatted string."""
    return string.format_map(SafeDict(**words))
