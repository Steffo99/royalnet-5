import discord
from discord.ext import commands
import db
import re
import errors

# Init the event loop
import asyncio
loop = asyncio.get_event_loop()

# Init the config reader
import configparser
config = configparser.ConfigParser()
config.read("config.ini")

# Init the discord bot
client = discord.Client()

@client.event
async def on_message(message: discord.Message):
    if message.content.startswith("!register"):
        try:
            username = message.content.split(" ", 1)[1]
        except IndexError:
            await client.send_message(message.channel, "⚠️ Non hai specificato un username!")
            return
        try:
            d = db.Discord.create(royal_username=username,
                                  discord_user=message.author)
        except errors.AlreadyExistingError:
            await client.send_message(message.channel, "⚠ Il tuo account Discord è già collegato a un account RYG o l'account RYG che hai specificato è già collegato a un account Discord.")
            return
        db.session.add(d)
        db.session.commit()
        await client.send_message(message.channel, "✅ Sincronizzazione completata!")

client.run(config["Discord"]["bot_token"])
db.session.close()