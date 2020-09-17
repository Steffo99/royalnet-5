import re
from typing import *
from ...utils import escalating_odds
import datetime


# https://stackoverflow.com/questions/18621568/regex-replace-text-outside-html-tags
spooky_pattern = re.compile(r"o(?![^\[]*]|[^[]]*\[/)")
spooky_replacement = r'⊕'

url_pattern = re.compile(r"\[url=(.*?)](.*?)\[/url]")
url_replacement = r'<a href="\1">\2</a>'


def escape(string: Optional[str]) -> Optional[str]:
    """Escape a string to be sent through Telegram (as HTML), and format it using RoyalCode.

    Warning:
        Currently escapes everything, even items in code blocks."""

    string = string.replace("<", "&lt;").replace(">", "&gt;")

    if escalating_odds(datetime.datetime(2020, 10, 17, 4, 0)):
        string = re.sub(spooky_pattern, spooky_replacement, string)

    string = string \
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

    string = re.sub(url_pattern, url_replacement, string)

    return string
