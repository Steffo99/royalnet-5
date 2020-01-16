def escape(string: str) -> str:
    """Escape a string to be sent through Matrix, and format it using RoyalCode.

    Underlines are currently unsupported.

    Warning:
        Currently escapes everything, even items in code blocks."""
    return string.replace("[b]", "**") \
        .replace("[/b]", "**") \
        .replace("[i]", "_") \
        .replace("[/i]", "_") \
        .replace("[c]", "`") \
        .replace("[/c]", "`") \
        .replace("[p]", "```") \
        .replace("[/p]", "```")
