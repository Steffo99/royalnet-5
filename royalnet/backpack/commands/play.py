from royalnet.commands import *

try:
    import discord
except ImportError:
    discord = None


class PlayCommand(Command):
    # TODO: possibly move this in another pack

    name: str = "play"

    description = "Download a file located at an URL and play it on Discord."

    syntax = "[url]"

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        if self.interface.name != "discord":
            raise UnsupportedError()
        msg: "discord.Message" = data.message
        guild: "discord.Guild" = msg.guild
        url: str = args.joined()
        response: dict = await self.interface.call_herald_event("discord", "play", {
            "guild_id": guild.id,
            "url": url,
        })
        await data.reply(f"✅ !")
