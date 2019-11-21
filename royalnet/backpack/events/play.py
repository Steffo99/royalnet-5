from typing import Optional
from royalnet.commands import *
from royalnet.serf.discord import DiscordSerf
from royalnet.serf.discord.discordbard import YtdlDiscord, DiscordBard
from royalnet.utils import asyncify
import logging

log = logging.getLogger(__name__)

try:
    import discord
except ImportError:
    discord = None


class PlayEvent(Event):
    name = "play"

    async def run(self, *, url: str, guild_id: Optional[int] = None, guild_name: Optional[str] = None, **kwargs):
        if not isinstance(self.serf, DiscordSerf):
            raise UnsupportedError("Play can't be called on interfaces other than Discord.")
        if discord is None:
            raise UnsupportedError("'discord' extra is not installed.")
        # Variables
        client = self.serf.client
        # Find the guild
        guild: Optional["discord.Guild"] = None
        if guild_id is not None:
            guild = client.get_guild(guild_id)
        elif guild_name is not None:
            for g in client.guilds:
                if g.name == guild_name:
                    guild = g
                    break
        if guild is None:
            raise InvalidInputError("No guild_id or guild_name specified.")
        # Find the bard
        bard: Optional[DiscordBard] = self.serf.bards.get(guild)
        if bard is None:
            raise CommandError("Bot is not connected to voice chat.")
        # Create the YtdlDiscords
        log.debug(f"Downloading: {url}")
        try:
            ytdl = await YtdlDiscord.from_url(url)
        except Exception as exc:
            breakpoint()
            return
        # Add the YtdlDiscords to the queue
        log.debug(f"Adding to bard: {ytdl}")
        for ytd in ytdl:
            await bard.add(ytd)
        # Run the bard
        log.debug(f"Running voice for: {guild}")
        await self.serf.voice_run(guild)
