class SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def safeformat(string: str, ignore_escaping: bool = False, **words: str) -> str:
    if ignore_escaping:
        escaped = words
    else:
        escaped = {}
        for key in words:
            escaped[key] = str(words[key]).replace("<", "&lt;").replace(">", "&gt;")
    return string.format_map(SafeDict(**escaped))
