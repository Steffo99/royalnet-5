import typing
import discord
import asyncio
import datetime
from ..command import Command
from ..commandinterface import CommandInterface
from ..commandargs import CommandArgs
from ..commanddata import CommandData
from ...utils import NetworkHandler, asyncify
from ...network import Request, ResponseSuccess
from ..commanderrors import CommandError, InvalidInputError, UnsupportedError, KeyboardExpiredError
from ...audio import YtdlDiscord
from ...audio.playmodes import Playlist
if typing.TYPE_CHECKING:
    from ...bots import DiscordBot


class ZawarudoNH(NetworkHandler):
    message_type = "music_zawarudo"

    ytdl_args = {
        "format": "bestaudio/best",
        "outtmpl": f"./downloads/%(title)s.%(ext)s"
    }

    @classmethod
    async def discord(cls, bot: "DiscordBot", data: dict):
        # Find the matching guild
        if data["guild_name"]:
            guilds: typing.List[discord.Guild] = bot.client.find_guild_by_name(data["guild_name"])
        else:
            guilds = bot.client.guilds
        if len(guilds) == 0:
            raise CommandError("No guilds with the specified name found.")
        if len(guilds) > 1:
            raise CommandError("Multiple guilds with the specified name found.")
        guild = list(bot.client.guilds)[0]
        # Ensure the guild has a PlayMode before adding the file to it
        if not bot.music_data.get(guild):
            # TODO: change Exception
            raise Exception("No music_data for this guild")
        # Create url
        ytdl_args = {
            "format": "bestaudio",
            "outtmpl": f"./downloads/{datetime.datetime.now().timestamp()}_%(title)s.%(ext)s"
        }
        # Start downloading
        zw_start: typing.List[YtdlDiscord] = await asyncify(YtdlDiscord.create_from_url,
                                                            "https://scaleway.steffo.eu/jojo/zawarudo_intro.mp3",
                                                            **ytdl_args)
        zw_end: typing.List[YtdlDiscord] = await asyncify(YtdlDiscord.create_from_url,
                                                          "https://scaleway.steffo.eu/jojo/zawarudo_outro.mp3",
                                                          **ytdl_args)
        old_playlist = bot.music_data[guild]
        bot.music_data[guild] = Playlist()
        # Get voice client
        vc: discord.VoiceClient = bot.client.find_voice_client_by_guild(guild)
        channel: discord.VoiceChannel = vc.channel
        affected: typing.List[typing.Union[discord.User, discord.Member]] = channel.members
        await bot.add_to_music_data(zw_start, guild)
        for member in affected:
            if member.bot:
                continue
            await member.edit(mute=True)
        await asyncio.sleep(data["time"])
        await bot.add_to_music_data(zw_end, guild)
        for member in affected:
            member: typing.Union[discord.User, discord.Member]
            if member.bot:
                continue
            await member.edit(mute=False)
        bot.music_data[guild] = old_playlist
        await bot.advance_music_data(guild)
        return ResponseSuccess()


class ZawarudoCommand(Command):
    name: str = "zawarudo"

    aliases = ["theworld", "world"]

    description: str = "Ferma il tempo!"

    syntax = "[ [guild] ] [1-9]"

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        interface.register_net_handler(ZawarudoNH.message_type, ZawarudoNH)

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        guild_name, time = args.match(r"(?:\[(.+)])?\s*(.+)?")
        if time is None:
            time = 5
        else:
            time = int(time)
        if time < 1:
            raise InvalidInputError("The World can't stop time for less than a second.")
        if time > 10:
            raise InvalidInputError("The World can stop time only for 10 seconds.")
        await data.reply(f"🕒 ZA WARUDO! TOKI WO TOMARE!")
        await self.interface.net_request(Request(ZawarudoNH.message_type, {"time": time, "guild_name": guild_name}), "discord")
