import re


def escape(string: str) -> str:
    """Escape a string to be sent through Telegram (as HTML), and format it using RoyalCode.

    Warning:
        Currently escapes everything, even items in code blocks."""
    url_pattern = re.compile(r"\[url=(.*?)](.*?)\[/url]")
    url_replacement = r'<a href="\1">\2</a>'

    escaped_string = string.replace("<", "&lt;").replace(">", "&gt;")

    simple_parse = escaped_string \
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

    advanced_parse = re.sub(url_pattern, url_replacement, simple_parse)

    return advanced_parse
