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
    # Open a new postgres session
    session = db.Session()
    try:
        if message.content.startswith("!register"):
            try:
                username = message.content.split(" ", 1)[1]
            except IndexError:
                await client.send_message(message.channel, "⚠️ Non hai specificato un username!")
                return
            try:
                d = db.Discord.create(session,
                                      royal_username=username,
                                      discord_user=message.author)
            except errors.AlreadyExistingError:
                await client.send_message(message.channel, "⚠ Il tuo account Discord è già collegato a un account RYG o l'account RYG che hai specificato è già collegato a un account Discord.")
                return
            session.add(d)
            session.commit()
            await client.send_message(message.channel, "✅ Sincronizzazione completata!")
    finally:
        session.close()


async def update_users_pipe(users_connection):
    await client.wait_until_ready()
    while True:
        msg = await loop.run_in_executor(None, users_connection.recv)
        if msg == "/cv":
            discord_members = list(client.get_server(config["Discord"]["server_id"]).members)
            users_connection.send(discord_members)


def process(users_connection):
    print("Discordbot starting...")
    loop.create_task(update_users_pipe(users_connection))
    client.run(config["Discord"]["bot_token"])