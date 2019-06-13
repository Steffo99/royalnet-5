import typing
import asyncio
from ..utils import Command, Call, NetworkHandler
from ..network import Request, ResponseSuccess
from ..error import NoneFoundError, TooManyFoundError, CurrentlyDisabledError
from ..audio import Playlist, Pool
if typing.TYPE_CHECKING:
    from ..bots import DiscordBot


class PlaymodeNH(NetworkHandler):
    message_type = "music_playmode"

    @classmethod
    async def discord(cls, bot: "DiscordBot", data: dict):
        """Handle a playmode Royalnet request. That is, change current PlayMode."""
        # Find the matching guild
        if data["guild_name"]:
            guild = bot.client.find_guild(data["guild_name"])
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
        if data["mode_name"] == "playlist":
            bot.music_data[guild] = Playlist()
        elif data["mode_name"] == "pool":
            # bot.music_data[guild] = Pool()
            raise CurrentlyDisabledError("Bug: https://github.com/royal-games/royalnet/issues/61")
        else:
            raise ValueError("No such PlayMode")
        return ResponseSuccess()


class PlaymodeCommand(Command):
    command_name = "playmode"
    command_description = "Cambia modalità di riproduzione per la chat vocale."
    command_syntax = "[ [guild] ] (mode)"

    network_handlers = [PlaymodeNH]

    @classmethod
    async def common(cls, call: Call):
        guild_name, mode_name = call.args.match(r"(?:\[(.+)])?\s*(\S+)\s*")
        await call.net_request(Request("music_playmode", {"mode_name": mode_name, "guild_name": guild_name}), "discord")
        await call.reply(f"✅ Modalità di riproduzione [c]{mode_name}[/c].")
