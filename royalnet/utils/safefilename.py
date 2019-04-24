import re


def safefilename(string: str):
    """Ensure a string can be used as a filename by replacing all non-word characters with underscores."""
    return re.sub(r"\W", "_", string)
