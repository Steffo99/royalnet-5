def escape(string: str) -> str:
    """Escape a string to be sent through Discord, and format it using RoyalCode.

    Warning:
        Currently escapes everything, even items in code blocks."""
    return string.replace("*", "\\*") \
        .replace("_", "\\_") \
        .replace("`", "\\`") \
        .replace("[b]", "**") \
        .replace("[/b]", "**") \
        .replace("[i]", "_") \
        .replace("[/i]", "_") \
        .replace("[u]", "__") \
        .replace("[/u]", "__") \
        .replace("[c]", "`") \
        .replace("[/c]", "`") \
        .replace("[p]", "```") \
        .replace("[/p]", "```")
