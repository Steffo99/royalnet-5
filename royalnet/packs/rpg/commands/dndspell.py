import aiohttp
import sortedcontainers
from royalnet.commands import *
from royalnet.utils import ordinalformat, andformat
from ..utils import parse_5etools_entry


class DndspellCommand(Command):
    name: str = "dndspell"

    aliases = ["spell"]

    description: str = "Ottieni informazioni su una magia di D&D5e."

    syntax = "{nomemagia}"

    _dnddata: sortedcontainers.SortedKeyList = None

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        interface.loop.create_task(self._fetch_dnddata())

    async def _fetch_dnddata(self):
        self._dnddata = self._dnddata = sortedcontainers.SortedKeyList([], key=lambda i: i["name"].lower())
        async with aiohttp.ClientSession() as session:
            for url in [
                "https://5e.tools/data/spells/spells-ai.json",
                "https://5e.tools/data/spells/spells-ggr.json",
                "https://5e.tools/data/spells/spells-llk.json",
                "https://5e.tools/data/spells/spells-phb.json",
                "https://5e.tools/data/spells/spells-scag.json",
                "https://5e.tools/data/spells/spells-stream.json",
                "https://5e.tools/data/spells/spells-ua-ar.json",
                "https://5e.tools/data/spells/spells-ua-mm.json",
                "https://5e.tools/data/spells/spells-ua-ss.json",
                "https://5e.tools/data/spells/spells-ua-tobm.json",
                "https://5e.tools/data/spells/spells-xge.json"
            ]:
                async with session.get(url) as response:
                    j = await response.json()
                    for spell in j["spell"]:
                        self._dnddata.add(spell)

    @staticmethod
    def _parse_spell(spell: dict) -> str:
        string = f'✨ [b]{spell["name"]}[/b]\n'
        if "source" in spell:
            string += f'[i]{spell["source"]}, page {spell["page"]}[/i]\n'
        string += "\n"
        if spell["level"] == 0:
            string += f'[b]Cantrip[/b] {spell["school"]}\n'
        else:
            string += f'[b]{ordinalformat(spell["level"])}[/b] level {spell["school"]}\n'
        if "time" in spell:
            for time in spell["time"]:
                string += f'Cast time: ⌛️ [b]{time["number"]} {time["unit"]}[/b]\n'
        if "range" in spell:
            if spell["range"]["distance"]["type"] == "touch":
                string += "Range: 👉 [b]Touch[/b]\n"
            elif spell["range"]["distance"]["type"] == "self":
                string += "Range: 👤 [b]Self[/b]\n"
            else:
                string += f'Range: 🏹 [b]{spell["range"]["distance"]["amount"]} {spell["range"]["distance"]["type"]}[/b] ({spell["range"]["type"]})\n'
        if "components" in spell:
            string += f'Components: '
            if spell["components"].get("v", False):
                string += "👄 [b]Verbal[/b] | "
            if spell["components"].get("s", False):
                string += "🤙 [b]Somatic[/b] | "
            if spell["components"].get("r", False):
                # TODO: wtf is this
                string += "❓ [b]R...?[/b] | "
            if spell["components"].get("m", False):
                if "text" in spell["components"]["m"]:
                    string += f'💎 [b]Material[/b] ([i]{spell["components"]["m"]["text"]}[/i]) | '
                else:
                    string += f'💎 [b]Material[/b] ([i]{spell["components"]["m"]}[/i]) | '
                string = string.rstrip(" ").rstrip("|")
            string += "\n"
        string += "\n"
        if "duration" in spell:
            for duration in spell["duration"]:
                if duration["type"] == "timed":
                    string += f'Duration: 🕒 [b]{duration["duration"]["amount"]} {duration["duration"]["type"]}[/b]'
                elif duration["type"] == "instant":
                    string += 'Duration: ☁️ [b]Instantaneous[/b]'
                elif duration["type"] == "special":
                    string += 'Duration: ⭐️ [b]Special[/b]'
                elif duration["type"] == "permanent":
                    string += f"Duration: ♾ [b]Permanent[/b] (ends on {andformat(duration['ends'], final=' or ')})"
                else:
                    string += f'Duration: ⚠️[b]UNKNOWN[/b]'
                if duration.get("concentration", False):
                    string += " (requires concentration)"
                string += "\n"
        if "meta" in spell:
            if spell["meta"].get("ritual", False):
                string += "🔮 Can be casted as ritual\n"
        string += "\n"
        for entry in spell.get("entries", []):
            string += parse_5etools_entry(entry)
            string += "\n\n"
        for entry in spell.get("entriesHigherLevel", []):
            string += parse_5etools_entry(entry)
            string += "\n\n"
        return string

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        if self._dnddata is None:
            await data.reply("⚠️ Il database degli oggetti di D&D non è ancora stato scaricato.")
            return
        search = args.joined().lower()
        result = self._dnddata[self._dnddata.bisect_key_left(search)]
        await data.reply(self._parse_spell(result))
