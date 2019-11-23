from typing import Optional
from royalnet.commands import *
from royalnet.serf.discord import DiscordSerf, PlayableYTDQueue
from royalnet.bard import YtdlDiscord

try:
    import discord
except ImportError:
    discord = None


class PlayEvent(Event):
    name = "play"

    async def run(self, *, url: str):
        if not isinstance(self.serf, DiscordSerf):
            raise UnsupportedError("Summon can't be called on interfaces other than Discord.")
        if discord is None:
            raise UnsupportedError("'discord' extra is not installed.")
        ytd = await YtdlDiscord.from_url(url)
        self.serf.voice_players[0].playing.contents.append(ytd[0])
        await self.serf.voice_players[0].start()
        return {"ok": "ok"}