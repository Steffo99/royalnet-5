import typing
import pickle
import discord
from ..command import Command
from ..commandinterface import CommandInterface
from ..commandargs import CommandArgs
from ..commanddata import CommandData
from ...utils import NetworkHandler, numberemojiformat
from ...network import Request, ResponseSuccess
from ..commanderrors import CommandError
if typing.TYPE_CHECKING:
    from ...bots import DiscordBot


class QueueNH(NetworkHandler):
    message_type = "music_queue"

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
                "strings": [str(dfile.info) for dfile in queue],
                "pickled_embeds": str(pickle.dumps([dfile.info.to_discord_embed() for dfile in queue]))
            }
        })


class QueueCommand(Command):
    name: str = "queue"

    aliases = ["q"]

    description: str = "Visualizza la coda di riproduzione attuale."

    syntax = "[ [guild] ]"

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        interface.register_net_handler(QueueNH.message_type, QueueNH)

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        guild, = args.match(r"(?:\[(.+)])?")
        response = await self.interface.net_request(Request(QueueNH.message_type, {"guild_name": guild}), "discord")
        if response["type"] is None:
            await data.reply("ℹ️ Non c'è nessuna coda di riproduzione attiva al momento.")
            return
        elif "queue" not in response:
            await data.reply(f"ℹ️ La coda di riproduzione attuale ([c]{response['type']}[/c]) non permette l'anteprima.")
            return
        if response["type"] == "Playlist":
            if len(response["queue"]["strings"]) == 0:
                message = f"ℹ️ Questa [c]Playlist[/c] è vuota."
            else:
                message = f"ℹ️ Questa [c]Playlist[/c] contiene {len(response['queue']['strings'])} elementi, e i prossimi saranno:\n"
        elif response["type"] == "Pool":
            if len(response["queue"]["strings"]) == 0:
                message = f"ℹ️ Questo [c]Pool[/c] è vuoto."
            else:
                message = f"ℹ️ Questo [c]Pool[/c] contiene {len(response['queue']['strings'])} elementi, tra cui:\n"
        elif response["type"] == "Layers":
            if len(response["queue"]["strings"]) == 0:
                message = f"ℹ️ Nessun elemento è attualmente in riproduzione, pertanto non ci sono [c]Layers[/c]:"
            else:
                message = f"ℹ️ I [c]Layers[/c] dell'elemento attualmente in riproduzione sono {len(response['queue']['strings'])}, tra cui:\n"
        else:
            if len(response["queue"]["strings"]) == 0:
                message = f"ℹ️ Il PlayMode attuale, [c]{response['type']}[/c], è vuoto.\n"
            else:
                message = f"ℹ️ Il PlayMode attuale, [c]{response['type']}[/c], contiene {len(response['queue']['strings'])} elementi:\n"
        if self.interface.name == "discord":
            await data.reply(message)
            for embed in pickle.loads(eval(response["queue"]["pickled_embeds"]))[:5]:
                await data.message.channel.send(embed=embed)
        else:
            message += numberemojiformat(response["queue"]["strings"][:10])
            await data.reply(message)
