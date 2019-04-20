import re


def safefilename(string: str):
    return re.sub(r"\W", "_", string)
