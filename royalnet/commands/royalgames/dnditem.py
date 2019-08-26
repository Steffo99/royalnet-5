import typing
import aiohttp
import sortedcontainers
from ..command import Command
from ..commandargs import CommandArgs
from ..commanddata import CommandData
from ..commandinterface import CommandInterface


class DnditemCommand(Command):
    name: str = "dnditem"

    description: str = "Ottieni informazioni su un oggetto di D&D5e."

    syntax = "(nomeoggetto)"

    _dnddata: sortedcontainers.SortedKeyList = None

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        interface.loop.create_task(self._fetch_dnddata())

    async def _fetch_dnddata(self):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://scaleway.steffo.eu/dnd/items.json") as response:
                j = await response.json()
        self._dnddata = sortedcontainers.SortedKeyList(j["item"], key=lambda i: i["name"].lower())

    def _parse_entry(self, entry):
        if isinstance(entry, str):
            return entry
        elif isinstance(entry, dict):
            string = ""
            if entry["type"] == "entries":
                string += f'[b]{entry.get("name", "")}[/b]\n'
                for subentry in entry["entries"]:
                    string += self._parse_entry(subentry)
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
                return self._parse_entry(entry["entry"])
            else:
                string += "[i][unknown type][/i]"
        else:
            return "[/i][unknown data][/i]"
        return string

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        if self._dnddata is None:
            await data.reply("⚠️ Il database degli oggetti di D&D non è ancora stato scaricato.")
            return
        search = args.joined().lower()
        result = self._dnddata[self._dnddata.bisect_key_left(search)]
        string = f'[b]{result["name"]}[/b]\n' \
                 f'[i]{result["source"]}, page {result["page"]}[/i]\n' \
                 f'\n' \
                 f'Type: [b]{result.get("type", "None")}[/b]\n' \
                 f'Value: [b]{result.get("value", "Priceless")}[/b]\n' \
                 f'Weight: [b]{result.get("weight", "0")} lb[/b]\n' \
                 f'Rarity: [b]{result["rarity"] if result["rarity"] != "None" else "Mundane"}[/b]\n' \
                 f'\n'
        for entry in result.get("entries", []):
            string += self._parse_entry(entry)
            string += "\n\n"
        await data.reply(string)
