import re
from ...utils import escalating_odds
import datetime


# https://stackoverflow.com/questions/18621568/regex-replace-text-outside-html-tags
spooky_pattern = re.compile(r"o(?![^\[]*]|[^[]]*\[/)")
spooky_replacement = r'⊕'

url_pattern = re.compile(r"\[url=(.*?)](.*?)\[/url]")
url_replacement = r'\2 (\1)'


def escape(string: str) -> str:
    """Escape a string to be sent through Discord, and format it using RoyalCode.

    Warning:
        Currently escapes everything, even items in code blocks."""
    if escalating_odds(datetime.datetime(2020, 10, 17, 4, 0)):
        string = re.sub(spooky_pattern, spooky_replacement, string)

    string = string \
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

    string = re.sub(url_pattern, url_replacement, string)

    return string
