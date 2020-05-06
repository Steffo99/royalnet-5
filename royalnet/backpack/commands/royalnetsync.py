from typing import *
import royalnet
import royalnet.commands as rc
import royalnet.utils as ru
from ..tables.telegram import Telegram
from ..tables.discord import Discord


class RoyalnetsyncCommand(rc.Command):
    name: str = "royalnetsync"

    description: str = "Connect your chat account to Royalnet!"

    syntax: str = "{username} {password}"

    async def run(self, args: rc.CommandArgs, data: rc.CommandData) -> None:
        username = args[0]
        password = " ".join(args[1:])

        author = await data.get_author(error_if_none=True)

        user = await data.find_user(username)
        try:
            successful = user.test_password(password)
        except ValueError:
            raise rc.UserError(f"User {user} has no password set!")
        if not successful:
            raise rc.InvalidInputError(f"Invalid password!")

        if self.interface.name == "telegram":
            import telegram
            message: telegram.Message = data.message
            from_user: telegram.User = message.from_user
            TelegramT = self.alchemy.get(Telegram)
            tg_user: Telegram = await ru.asyncify(
                data.session.query(TelegramT).filter_by(tg_id=from_user.id).one_or_none
            )
            if tg_user is None:
                # Create
                tg_user = TelegramT(
                    user=author,
                    tg_id=from_user.id,
                    first_name=from_user.first_name,
                    last_name=from_user.last_name,
                    username=from_user.username
                )
                data.session.add(tg_user)
            else:
                # Edit
                tg_user.first_name = from_user.first_name
                tg_user.last_name = from_user.last_name
                tg_user.username = from_user.username
            await data.session_commit()
            await data.reply(f"↔️ Account {tg_user} synced to {author}!")

        elif self.interface.name == "discord":
            import discord
            message: discord.Message = data.message
            author: discord.User = message.author
            DiscordT = self.alchemy.get(Discord)
            ds_user: Discord = await ru.asyncify(
                data.session.query(DiscordT).filter_by(discord_id=author.id).one_or_none
            )
            if ds_user is None:
                # Create
                ds_user = DiscordT(
                    user=author,
                    discord_id=author.id,
                    username=author.name,
                    discriminator=author.discriminator,
                    avatar_url=author.avatar_url
                )
                data.session.add(ds_user)
            else:
                # Edit
                ds_user.username = author.name
                ds_user.discriminator = author.discriminator
                ds_user.avatar_url = author.avatar_url
            await data.session_commit()
            await data.reply(f"↔️ Account {ds_user} synced to {author}!")

        elif self.interface.name == "matrix":
            raise rc.UnsupportedError(f"{self} hasn't been implemented for Matrix yet")

        else:
            raise rc.UnsupportedError(f"Unknown interface: {self.interface.name}")
