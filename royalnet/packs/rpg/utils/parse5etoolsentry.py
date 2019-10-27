def parse_5etools_entry(entry) -> str:
    if isinstance(entry, str):
        return entry
    elif isinstance(entry, dict):
        string = ""
        if entry["type"] == "entries":
            string += f'[b]{entry.get("name", "")}[/b]\n'
            for subentry in entry["entries"]:
                string += parse_5etools_entry(subentry)
                string += "\n\n"
        elif entry["type"] == "table":
            string += "[i][table hidden][/i]"
            # for label in entry["colLabels"]:
            #     string += f"| {label} "
            # string += "|"
            # for row in entry["rows"]:
            #     for column in row:
            #         string += f"| {self._parse_entry(column)} "
            #     string += "|\n"
        elif entry["type"] == "cell":
            return parse_5etools_entry(entry["entry"])
        elif entry["type"] == "list":
            string = ""
            for item in entry["items"]:
                string += f"- {parse_5etools_entry(item)}\n"
            string.rstrip("\n")
        else:
            string += "[i]⚠️ [unknown type][/i]"
    else:
        return "[/i]⚠️ [unknown data][/i]"
    return string
