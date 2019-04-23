import typing
import asyncio
from ..utils import Command, Call, NetworkHandler
from ..network import Message, RequestSuccessful
from ..error import NoneFoundError, TooManyFoundError
from ..audio import Playlist, Pool
if typing.TYPE_CHECKING:
    from ..bots import DiscordBot


loop = asyncio.get_event_loop()


class PlaymodeMessage(Message):
    def __init__(self, mode_name: str, guild_name: typing.Optional[str] = None):
        self.mode_name: str = mode_name
        self.guild_name: typing.Optional[str] = guild_name


class PlaymodeNH(NetworkHandler):
    message_type = PlaymodeMessage

    @classmethod
    async def discord(cls, bot: "DiscordBot", message: PlaymodeMessage):
        """Handle a playmode Royalnet request. That is, change current PlayMode."""
        # Find the matching guild
        if message.guild_name:
            guild = bot.client.find_guild(message.guild_name)
        else:
            if len(bot.music_data) == 0:
                raise NoneFoundError("No voice clients active")
            if len(bot.music_data) > 1:
                raise TooManyFoundError("Multiple guilds found")
            guild = list(bot.music_data)[0]
        # Delete the previous PlayMode, if it exists
        if bot.music_data[guild] is not None:
            bot.music_data[guild].delete()
        # Create the new PlayMode
        if message.mode_name == "playlist":
            bot.music_data[guild] = Playlist()
        elif message.mode_name == "pool":
            bot.music_data[guild] = Pool()
        else:
            raise ValueError("No such PlayMode")
        return RequestSuccessful()


class PlaymodeCommand(Command):
    command_name = "playmode"
    command_description = "Cambia modalità di riproduzione per la chat vocale."
    command_syntax = "[ [guild] ] (mode)"

    network_handlers = [PlaymodeNH]

    @classmethod
    async def common(cls, call: Call):
        guild, mode_name = call.args.match(r"(?:\[(.+)])?\s*(\S+)\s*")
        await call.net_request(PlaymodeMessage(mode_name, guild), "discord")
        await call.reply(f"✅ Richiesto di passare alla modalità di riproduzione [c]{mode_name}[/c].")
