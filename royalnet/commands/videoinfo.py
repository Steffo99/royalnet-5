import asyncio
from ..utils import Command, Call, asyncify
from ..audio import YtdlInfo


class VideoinfoCommand(Command):

    command_name = "videoinfo"
    command_description = "Scarica e visualizza le informazioni di un video."
    command_syntax = ""

    @classmethod
    async def common(cls, call: Call):
        url = call.args[0]
        info_list = await asyncify(YtdlInfo.create_from_url, url)
        for info in info_list:
            info_dict = info.__dict__
            message = f"🔍 Dati di [b]{info}[/b]:\n"
            for key in __dict__:
                if info_dict[key] is None:
                    continue
                message += f"{key}: [b]{info_dict[key]}[/b]\n"
            await call.reply(message)
            await asyncio.sleep(0.2)
