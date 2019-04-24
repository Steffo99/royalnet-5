def plusformat(i: int) -> str:
    """Convert an :py:class:`int` to a string, adding a plus if they are greater than 0.

    Parameters:
        i: the :py:class:`int` to convert

    Returns:
        The resulting :py:class:`str`"""
    if i >= 0:
        return f"+{i}"
    return str(i)
