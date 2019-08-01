import asyncio
import typing
import urllib.parse
from ..utils import Command, Call, asyncify
from ..audio import YtdlVorbis


ytdl_args = {
    "format": "bestaudio",
    "outtmpl": f"./downloads/%(epoch)s_%(title)s.%(ext)s"
}


seconds_before_deletion = 15*60


class DlmusicCommand(Command):

    command_name = "dlmusic"
    command_description = "Scarica un video."
    command_syntax = "(url)"

    @classmethod
    async def common(cls, call: Call):
        url = call.args[0]
        files: typing.List[YtdlVorbis] = await asyncify(YtdlVorbis.create_and_ready_from_url, url, **ytdl_args)
        for file in files:
            await call.reply(f"⬇️ https://scaleway.steffo.eu/musicbot_cache/{urllib.parse.quote(file.vorbis_filename)}")
        await asyncio.sleep(seconds_before_deletion)
        for file in files:
            file.delete()
