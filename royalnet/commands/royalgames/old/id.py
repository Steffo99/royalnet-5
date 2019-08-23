import telegram
import discord
import typing
from ..utils import Command, Call


class IdCommand(Command):

    command_name = "id"
    command_description = "Visualizza l'id della chat attuale."
    command_syntax = ""

    @classmethod
    async def telegram(cls, call: Call):
        chat: telegram.Chat = call.channel
        await call.reply(f"🔢 L'id di questa chat è [b]{chat.id}[/b].")

    @classmethod
    async def discord(cls, call: Call):
        channel = call.channel
        if isinstance(channel, discord.TextChannel):
            await call.reply(f"🔢 L'id di questa chat è [b]{channel.id}[/b].")
        elif isinstance(channel, discord.DMChannel):
            await call.reply(f"🔢 L'id di questa chat è [b]{channel.id}[/b].")
        else:
            await call.reply(f"⚠️ Questo tipo di chat non è supportato.")
