import typing
import pickle
from ..network import Request, ResponseSuccess
from ..utils import Command, Call, NetworkHandler, numberemojiformat
from ..error import TooManyFoundError, NoneFoundError
if typing.TYPE_CHECKING:
    from ..bots import DiscordBot


class QueueNH(NetworkHandler):
    message_type = "music_queue"

    @classmethod
    async def discord(cls, bot: "DiscordBot", data: dict):
        # Find the matching guild
        if data["guild_name"]:
            guild = bot.client.find_guild_by_name(data["guild_name"])
        else:
            if len(bot.music_data) == 0:
                raise NoneFoundError("No voice clients active")
            if len(bot.music_data) > 1:
                raise TooManyFoundError("Multiple guilds found")
            guild = list(bot.music_data)[0]
        # Check if the guild has a PlayMode
        playmode = bot.music_data.get(guild)
        if not playmode:
            return ResponseSuccess({
                "type": None
            })
        try:
            queue = playmode.queue_preview()
        except NotImplementedError:
            return ResponseSuccess({
                "type": playmode.__class__.__name__
            })
        return ResponseSuccess({
            "type": playmode.__class__.__name__,
            "queue":
            {
                "strings": [str(element.rpf.info) for element in queue],
                "pickled_embeds": str(pickle.dumps([element.rpf.info.to_discord_embed() for element in queue]))
            }
        })


class QueueCommand(Command):

    command_name = "queue"
    command_description = "Visualizza un'anteprima della coda di riproduzione attuale."
    command_syntax = "[ [guild] ]"

    network_handlers = [QueueNH]

    @classmethod
    async def common(cls, call: Call):
        guild, = call.args.match(r"(?:\[(.+)])?")
        data = await call.net_request(Request("music_queue", {"guild_name": guild}), "discord")
        if data["type"] is None:
            await call.reply("ℹ️ Non c'è nessuna coda di riproduzione attiva al momento.")
            return
        elif "queue" not in data:
            await call.reply(f"ℹ️ La coda di riproduzione attuale ([c]{data['type']}[/c]) non permette l'anteprima.")
            return
        if data["type"] == "Playlist":
            if len(data["queue"]["strings"]) == 0:
                message = f"ℹ️ Questa [c]Playlist[/c] è vuota."
            else:
                message = f"ℹ️ Questa [c]Playlist[/c] contiene {len(data['queue']['strings'])} elementi, e i prossimi saranno:\n"
        elif data["type"] == "Pool":
            if len(data["queue"]["strings"]) == 0:
                message = f"ℹ️ Questo [c]Pool[/c] è vuoto."
            else:
                message = f"ℹ️ Questo [c]Pool[/c] contiene {len(data['queue']['strings'])} elementi, tra cui:\n"
        else:
            if len(data["queue"]["strings"]) == 0:
                message = f"ℹ️ Il PlayMode attuale, [c]{data['type']}[/c], è vuoto.\n"
            else:
                message = f"ℹ️ Il PlayMode attuale, [c]{data['type']}[/c], contiene {len(data['queue']['strings'])} elementi:\n"
        if call.interface_name == "discord":
            await call.reply(message)
            for embed in pickle.loads(eval(data["queue"]["pickled_embeds"]))[:5]:
                await call.channel.send(embed=embed)
        else:
            message += numberemojiformat(data["queue"]["strings"][:10])
            await call.reply(message)
