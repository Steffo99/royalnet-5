import asyncio
from ..utils import Command, Call, asyncify
from ..audio import YtdlInfo


class VideoinfoCommand(Command):

    command_name = "videoinfo"
    command_description = "Visualizza le informazioni di un video."
    command_syntax = "(url)"

    @classmethod
    async def common(cls, call: Call):
        url = call.args[0]
        info_list = await asyncify(YtdlInfo.create_from_url, url)
        for info in info_list:
            info_dict = info.__dict__
            message = f"🔍 Dati di [b]{info}[/b]:\n"
            for key in info_dict:
                # Skip description
                if key == "description":
                    continue
                # Skip formats
                if key == "formats":
                    continue
                if key == "requested_formats":
                    continue
                # Skip subtitles
                if key == "subtitles":
                    continue
                # Skip empty keys
                if info_dict[key] is None:
                    continue
                message += f"[c]{key}[/c]: {info_dict[key]}\n"
            await call.reply(message)
            await asyncio.sleep(0.2)
