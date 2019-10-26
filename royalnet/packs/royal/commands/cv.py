import discord
import typing
from royalnet.commands import *
from royalnet.utils import andformat
from royalnet.bots import DiscordBot


class CvCommand(Command):
    name: str = "cv"

    description: str = "Elenca le persone attualmente connesse alla chat vocale."

    syntax: str = "[guildname] [all]"

    @staticmethod
    async def _legacy_cv_handler(bot: DiscordBot, guild_name: typing.Optional[str], everyone: bool):
        # Find the matching guild
        if guild_name:
            guilds: typing.List[discord.Guild] = bot.client.find_guild_by_name(guild_name)
        else:
            guilds = bot.client.guilds
        if len(guilds) == 0:
            raise CommandError("No guilds with the specified name found.")
        if len(guilds) > 1:
            raise CommandError("Multiple guilds with the specified name found.")
        guild = list(bot.client.guilds)[0]
        # Edit the message, sorted by channel
        discord_members = list(guild.members)
        channels = {0: None}
        members_in_channels = {0: []}
        message = ""
        # Find all the channels
        for member in discord_members:
            if member.voice is not None:
                channel = members_in_channels.get(member.voice.channel.id)
                if channel is None:
                    members_in_channels[member.voice.channel.id] = list()
                    channel = members_in_channels[member.voice.channel.id]
                    channels[member.voice.channel.id] = member.voice.channel
                channel.append(member)
            else:
                members_in_channels[0].append(member)
        # Edit the message, sorted by channel
        for channel in sorted(channels, key=lambda c: -c):
            members_in_channels[channel].sort(key=lambda x: x.nick if x.nick is not None else x.name)
            if channel == 0 and len(members_in_channels[0]) > 0:
                message += "[b]Non in chat vocale:[/b]\n"
            else:
                message += f"[b]In #{channels[channel].name}:[/b]\n"
            for member in members_in_channels[channel]:
                member: typing.Union[discord.User, discord.Member]
                # Ignore not-connected non-notable members
                if not everyone and channel == 0 and len(member.roles) < 2:
                    continue
                # Ignore offline members
                if member.status == discord.Status.offline and member.voice is None:
                    continue
                # Online status emoji
                if member.bot:
                    message += "🤖 "
                elif member.status == discord.Status.online:
                    message += "🔵 "
                elif member.status == discord.Status.idle:
                    message += "⚫ "
                elif member.status == discord.Status.dnd:
                    message += "🔴 "
                elif member.status == discord.Status.offline:
                    message += "⚪ "
                # Voice
                if channel != 0:
                    # Voice status
                    if member.voice.afk:
                        message += "💤 "
                    elif member.voice.self_deaf or member.voice.deaf:
                        message += "🔇 "
                    elif member.voice.self_mute or member.voice.mute:
                        message += "🔈 "
                    elif member.voice.self_video or member.voice.self_stream:
                        message += "🖥 "
                    else:
                        message += "🔊 "
                # Nickname
                # if member.nick is not None:
                #     message += f"[i]{member.nick}[/i]"
                # else:
                message += member.name
                # Game or stream
                if member.activity is not None:
                    if member.activity.type == discord.ActivityType.playing:
                        message += f" | 🎮 {member.activity.name}"
                        # Rich presence
                        try:
                            if member.activity.state is not None:
                                message += f" ({member.activity.state}" \
                                           f" | {member.activity.details})"
                        except AttributeError:
                            pass
                    elif member.activity.type == discord.ActivityType.streaming:
                        message += f" | 📡 {member.activity.url}"
                    elif member.activity.type == discord.ActivityType.listening:
                        if isinstance(member.activity, discord.Spotify):
                            if member.activity.title == member.activity.album:
                                message += f" | 🎧 {member.activity.title} ({andformat(member.activity.artists, final=' e ')})"
                            else:
                                message += f" | 🎧 {member.activity.title} ({member.activity.album} | {andformat(member.activity.artists, final=' e ')})"
                        else:
                            message += f" | 🎧 {member.activity.name}"
                    elif member.activity.type == discord.ActivityType.watching:
                        message += f" | 📺 {member.activity.name}"
                    else:
                        message += f" | ❓ Unknown activity"
                message += "\n"
            message += "\n"
        return {"response": message}

    _event_name = "_legacy_cv"

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        if interface.name == "discord":
            interface.register_herald_action(self._event_name, self._legacy_cv_handler)

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        # noinspection PyTypeChecker
        guild_name, everyone = args.match(r"(?:\[(.+)])?\s*(\S+)?\s*")
        response = await self.interface.call_herald_action("discord", self._event_name, {
                                                               "guild_name": guild_name,
                                                               "everyone": everyone
                                                           })
        await data.reply(response["response"])
