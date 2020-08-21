import royalnet.commands as rc
import royalnet.serf.discord as rsd
import royalnet.serf.telegram as rst
import royalnet.utils as ru
from ..tables.discord import Discord
from ..tables.telegram import Telegram


class RoyalnetsyncCommand(rc.Command):
    name: str = "royalnetsync"

    description: str = "Connect your chat account to Royalnet!"

    syntax: str = "{username} {password}"

    async def run(self, args: rc.CommandArgs, data: rc.CommandData) -> None:
        author = await data.get_author(error_if_none=False)
        if author is not None:
            raise rc.UserError(f"This account is already connected to {author}!")

        username = args[0]
        password = " ".join(args[1:])

        user = await data.find_user(username)
        if user is None:
            raise rc.UserError("No such user.")
        try:
            successful = user.test_password(password)
        except ValueError:
            raise rc.UserError(f"User {user} has no password set!")
        if not successful:
            raise rc.InvalidInputError(f"Invalid password!")

        async with data.session_acm() as session:
            if isinstance(self.serf, rst.TelegramSerf):
                import telegram
                message: telegram.Message = data.message
                from_user: telegram.User = message.from_user
                TelegramT = self.alchemy.get(Telegram)
                tg_user: Telegram = await ru.asyncify(
                    session.query(TelegramT).filter_by(tg_id=from_user.id).one_or_none
                )
                if tg_user is None:
                    # Create
                    tg_user = TelegramT(
                        user=user,
                        tg_id=from_user.id,
                        first_name=from_user.first_name,
                        last_name=from_user.last_name,
                        username=from_user.username
                    )
                    session.add(tg_user)
                else:
                    # Edit
                    tg_user.first_name = from_user.first_name
                    tg_user.last_name = from_user.last_name
                    tg_user.username = from_user.username
                await ru.asyncify(session.commit)
                await data.reply(f"↔️ Account {tg_user} synced to {user}!")

            elif isinstance(self.serf, rsd.DiscordSerf):
                import discord
                message: discord.Message = data.message
                ds_author: discord.User = message.author
                DiscordT = self.alchemy.get(Discord)
                ds_user: Discord = await ru.asyncify(
                    session.query(DiscordT).filter_by(discord_id=ds_author.id).one_or_none
                )
                if ds_user is None:
                    # Create
                    # noinspection PyProtectedMember
                    ds_user = DiscordT(
                        user=user,
                        discord_id=ds_author.id,
                        username=ds_author.name,
                        discriminator=ds_author.discriminator,
                        avatar_url=ds_author.avatar_url._url
                    )
                    session.add(ds_user)
                else:
                    # Edit
                    ds_user.username = ds_author.name
                    ds_user.discriminator = ds_author.discriminator
                    ds_user.avatar_url = ds_author.avatar_url
                await ru.asyncify(session.commit)
                await data.reply(f"↔️ Account {ds_user} synced to {ds_author}!")

            else:
                raise rc.UnsupportedError(f"Unknown interface: {self.serf.__class__.__qualname__}")
