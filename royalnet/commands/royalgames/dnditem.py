import typing
import aiohttp
import sortedcontainers
from ..command import Command
from ..commandargs import CommandArgs
from ..commanddata import CommandData
from ..commandinterface import CommandInterface
from ...utils import parse_5etools_entry


class DnditemCommand(Command):
    name: str = "dnditem"

    aliases = ["item"]

    description: str = "Ottieni informazioni su un oggetto di D&D5e."

    syntax = "(nomeoggetto)"

    _dnddata: sortedcontainers.SortedKeyList = None

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        interface.loop.create_task(self._fetch_dnddata())

    async def _fetch_dnddata(self):
        self._dnddata = self._dnddata = sortedcontainers.SortedKeyList([], key=lambda i: i["name"].lower())
        async with aiohttp.ClientSession() as session:
            async with session.get("https://5e.tools/data/items.json") as response:
                j = await response.json()
                for item in j["item"]:
                    self._dnddata.add(item)
            async with session.get("https://5e.tools/data/fluff-items.json") as response:
                j = await response.json()
                for item in j["item"]:
                    self._dnddata.add(item)
            async with session.get("https://5e.tools/data/items-base.json") as response:
                j = await response.json()
                for item in j["baseitem"]:
                    self._dnddata.add(item)

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        if self._dnddata is None:
            await data.reply("⚠️ Il database degli oggetti di D&D non è ancora stato scaricato.")
            return
        search = args.joined().lower()
        result = self._dnddata[self._dnddata.bisect_key_left(search)]
        string = f'📦 [b]{result["name"]}[/b]\n'
        if "source" in result:
            string += f'[i]{result["source"]}, page {result["page"]}[/i]\n'
        string += f'\n' \
                  f'Type: [b]{result.get("type", "None")}[/b]\n' \
                  f'Value: [b]{result.get("value", "-")}[/b]\n' \
                  f'Weight: [b]{result.get("weight", "0")} lb[/b]\n' \
                  f'Rarity: [b]{result["rarity"] if result.get("rarity", "None") != "None" else "Mundane"}[/b]\n' \
                  f'\n'
        for entry in result.get("entries", []):
            string += parse_5etools_entry(entry)
            string += "\n\n"
        await data.reply(string)
