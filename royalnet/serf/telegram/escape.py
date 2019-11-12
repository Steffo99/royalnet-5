def escape(string: str) -> str:
    """Escape a string to be sent through Telegram (as HTML), and format it using RoyalCode.

    Warning:
        Currently escapes everything, even items in code blocks."""
    return string.replace("<", "&lt;") \
        .replace(">", "&gt;") \
        .replace("[b]", "<b>") \
        .replace("[/b]", "</b>") \
        .replace("[i]", "<i>") \
        .replace("[/i]", "</i>") \
        .replace("[u]", "<b>") \
        .replace("[/u]", "</b>") \
        .replace("[c]", "<code>") \
        .replace("[/c]", "</code>") \
        .replace("[p]", "<pre>") \
        .replace("[/p]", "</pre>")
