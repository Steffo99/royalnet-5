import re


def escape(string: str) -> str:
    """Escape a string to be sent through Discord, and format it using RoyalCode.

    Warning:
        Currently escapes everything, even items in code blocks."""
    url_pattern = re.compile(r"\[url=(.*?)](.*?)\[/url]")
    url_replacement = r'\2 (\1)'

    simple_parse = string \
        .replace("*", "\\*") \
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

    advanced_parse = re.sub(url_pattern, url_replacement, simple_parse)

    return advanced_parse
