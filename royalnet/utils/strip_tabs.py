import re


def strip_tabs(s: str) -> str:
    # https://github.com/Steffo99/bluelib/blob/pls-work/src/utils/stripTabs.js

    indent_regex = re.compile(r"^[ \t]+")

    rows = list(filter(lambda r: r != "", s.split("\n")))

    match = None
    for row in rows:
        match = re.match(indent_regex, row)
        if match is not None:
            break

    if match is None:
        start = 0
    else:
        start = len(match.group(0))

    return "\n".join(map(lambda r: r[start:], rows))
