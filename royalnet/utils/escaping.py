def discord_escape(string: str) -> str:
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


def telegram_escape(string: str) -> str:
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
