import typing
import discord
import asyncio
from ..command import Command
from ..commandinterface import CommandInterface
from ..commandargs import CommandArgs
from ..commanddata import CommandData
from ...utils import NetworkHandler, asyncify
from ...network import Request, ResponseSuccess
from ...error import *
from ...audio import YtdlDiscord
from ...audio.playmodes import Playlist
if typing.TYPE_CHECKING:
    from ...bots import DiscordBot


class ZawarudoNH(NetworkHandler):
    message_type = "music_zawarudo"

    ytdl_args = {
        "format": "bestaudio",
        "outtmpl": f"./downloads/%(title)s.%(ext)s"
    }

    @classmethod
    async def discord(cls, bot: "DiscordBot", data: dict):
        # Find the matching guild
        if data["guild_name"]:
            guild = bot.client.find_guild(data["guild_name"])
        else:
            if len(bot.music_data) == 0:
                raise NoneFoundError("No voice clients active")
            if len(bot.music_data) > 1:
                raise TooManyFoundError("Multiple guilds found")
            guild = list(bot.music_data)[0]
        # Ensure the guild has a PlayMode before adding the file to it
        if not bot.music_data.get(guild):
            # TODO: change Exception
            raise Exception("No music_data for this guild")
        # Start downloading
        zw_start: typing.List[YtdlDiscord] = await asyncify(YtdlDiscord.create_and_ready_from_url,
                                                            "https://scaleway.steffo.eu/jojo/zawarudo_intro.mp3",
                                                            **cls.ytdl_args)
        zw_end: typing.List[YtdlDiscord] = await asyncify(YtdlDiscord.create_and_ready_from_url,
                                                          "https://scaleway.steffo.eu/jojo/zawarudo_outro.mp3",
                                                          **cls.ytdl_args)
        # Clear playlist
        if bot.music_data[guild] is not None:
            bot.music_data[guild].delete()
        bot.music_data[guild] = Playlist()
        # Get voice client
        vc: discord.VoiceClient = bot.client.find_voice_client_by_guild(guild)
        channel: discord.VoiceChannel = vc.channel
        await bot.add_to_music_data(zw_start, guild)
        for member in channel.members:
            member: typing.Union[discord.User, discord.Member]
            if member.bot:
                continue
            await member.edit(mute=True)
        await asyncio.sleep(data["time"])
        await bot.add_to_music_data(zw_end, guild)
        for member in channel.members:
            member: typing.Union[discord.User, discord.Member]
            if member.bot:
                continue
            await member.edit(mute=False)
        return ResponseSuccess()


class ZawarudoCommand(Command):
    name: str = "zawarudo"

    description: str = "Ferma il tempo!"

    syntax = "[ [guild] ] [durata]"

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        interface.register_net_handler(ZawarudoNH.message_type, ZawarudoNH)

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        guild_name, time = args.match(r"(?:\[(.+)])?\s*(.+)?")
        if time is None:
            time = 5
        else:
            time = int(time)
        await data.reply(f"🕒 ZA WARUDO! TOKI WO TOMARE!")
        await self.interface.net_request(Request(ZawarudoNH.message_type, {"time": time, "guild_name": guild_name}), "discord")
