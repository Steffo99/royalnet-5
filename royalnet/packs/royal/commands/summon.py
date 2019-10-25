import typing
import discord
from royalnet.commands import *
from royalnet.bots import DiscordBot


class SummonCommand(Command):
    name: str = "summon"

    aliases = ["cv"]

    description: str = "Evoca il bot in un canale vocale."

    syntax: str = "[nomecanale]"

    @staticmethod
    async def _legacy_summon_handler(bot: "DiscordBot", channel_name: str):
        """Handle a summon Royalnet request.
         That is, join a voice channel, or move to a different one if that is not possible."""
        channels = bot.client.find_channel_by_name(channel_name)
        if len(channels) < 1:
            raise CommandError(f"Nessun canale vocale con il nome [c]{channel_name}[/c] trovato.")
        channel = channels[0]
        if not isinstance(channel, discord.VoiceChannel):
            raise CommandError(f"Il canale [c]{channel}[/c] non è un canale vocale.")
        bot.loop.create_task(bot.client.vc_connect_or_move(channel))
        return {}

    _event_name = "_legacy_summon"

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        if interface.name == "discord":
            interface.register_herald_action(self._event_name, self._legacy_summon_handler)

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        if self.interface.name == "discord":
            bot = self.interface.bot.client
            message: discord.Message = data.message
            channel_name: str = args.optional(0)
            if channel_name:
                guild: typing.Optional[discord.Guild] = message.guild
                if guild is not None:
                    channels: typing.List[discord.abc.GuildChannel] = guild.channels
                else:
                    channels = bot.get_all_channels()
                matching_channels: typing.List[discord.VoiceChannel] = []
                for channel in channels:
                    if isinstance(channel, discord.VoiceChannel):
                        if channel.name == channel_name:
                            matching_channels.append(channel)
                if len(matching_channels) == 0:
                    await data.reply("⚠️ Non esiste alcun canale vocale con il nome specificato.")
                    return
                elif len(matching_channels) > 1:
                    await data.reply("⚠️ Esiste più di un canale vocale con il nome specificato.")
                    return
                channel = matching_channels[0]
            else:
                author: discord.Member = message.author
                try:
                    voice: typing.Optional[discord.VoiceState] = author.voice
                except AttributeError:
                    await data.reply("⚠️ Non puoi evocare il bot da una chat privata!")
                    return
                if voice is None:
                    await data.reply("⚠️ Non sei connesso a nessun canale vocale!")
                    return
                channel = voice.channel
            await bot.vc_connect_or_move(channel)
            await data.reply(f"✅ Mi sono connesso in [c]#{channel.name}[/c].")
        else:
            channel_name: str = args[0].lstrip("#")
            response = await self.interface.call_herald_action("discord", self._event_name, {
                                                                   "channel_name": channel_name
                                                               })
            await data.reply(f"✅ Mi sono connesso in [c]#{channel_name}[/c].")
