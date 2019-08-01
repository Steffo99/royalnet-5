import telegram
import discord
import typing
from ..utils import Command, Call

class IdCommand(Command):

    command_name = "id"
    command_description = "Visualizza l'id della chat attuale."
    command_syntax = ""

    @classmethod
    def telegram(cls, call: Call):
        chat: telegram.Chat = call.channel
        call.reply(f"🔢 L'id di questa chat è [b]{chat.id}[/b].")

    @classmethod
    def discord(cls, call: Call):
        channel = call.channel
        if isinstance(channel, discord.TextChannel):
            call.reply(f"🔢 L'id di questa chat è [b]{channel.id}[/b].")
        elif isinstance(channel, discord.DMChannel):
            call.reply(f"🔢 L'id di questa chat è [b]{channel.id}[/b].")
        else:
            call.reply(f"⚠️ Questo tipo di chat non è supportato.")
