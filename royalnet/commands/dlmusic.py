import asyncio
import typing
import urllib.parse
from ..utils import Command, Call, asyncify
from ..audio import YtdlVorbis


ytdl_args = {
    "format": "bestaudio",
    "outtmpl": f"./downloads/%(title)s.%(ext)s"
}


seconds_before_deletion = 15*60


class DlmusicCommand(Command):

    command_name = "dlmusic"
    command_description = "Scarica un video."
    command_syntax = "(url)"

    @classmethod
    async def common(cls, call: Call):
        url = call.args.joined()
        if url.startswith("http://") or url.startswith("https://"):
            vfiles: typing.List[YtdlVorbis] = await asyncify(YtdlVorbis.create_and_ready_from_url, url, **ytdl_args)
        else:
            vfiles = await asyncify(YtdlVorbis.create_and_ready_from_url, f"ytsearch:{url}", **ytdl_args)
        for vfile in vfiles:
            await call.reply(f"⬇️ https://scaleway.steffo.eu/{urllib.parse.quote(vfile.vorbis_filename.replace('./downloads/', 'musicbot_cache/'))}")
        await asyncio.sleep(seconds_before_deletion)
        for vfile in vfiles:
            vfile.delete()
