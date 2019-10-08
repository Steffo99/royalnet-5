import typing
import urllib.parse
import asyncio
from ..command import Command
from ..commandargs import CommandArgs
from ..commanddata import CommandData
from ...utils import asyncify
from ...audio import YtdlMp3


class Mp3Command(Command):
    name: str = "mp3"

    description: str = "Scarica un video con youtube-dl e invialo in chat."

    syntax = "(ytdlstring)"

    ytdl_args = {
        "format": "bestaudio",
        "outtmpl": f"./downloads/%(title)s.%(ext)s"
    }

    seconds_before_deletion = 15 * 60

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        url = args.joined()
        if url.startswith("http://") or url.startswith("https://"):
            vfiles: typing.List[YtdlMp3] = await asyncify(YtdlMp3.create_and_ready_from_url,
                                                          url,
                                                          **self.ytdl_args)
        else:
            vfiles = await asyncify(YtdlMp3.create_and_ready_from_url, f"ytsearch:{url}", **self.ytdl_args)
        for vfile in vfiles:
            await data.reply(f"⬇️ Il file richiesto può essere scaricato a:\n"
                             f"https://scaleway.steffo.eu/{urllib.parse.quote(vfile.mp3_filename.replace('./downloads/', './musicbot_cache/'))}\n"
                             f"Verrà eliminato tra {self.seconds_before_deletion} secondi.")
        await asyncio.sleep(self.seconds_before_deletion)
        for vfile in vfiles:
            vfile.delete()
            await data.reply(f"⏹ Il file {vfile.info.title} è scaduto ed è stato eliminato.")
