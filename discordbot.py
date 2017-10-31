import discord
import discord.opus
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
discord.opus.load_opus("libopus-0.dll")
voice_client = None
voice_player = None

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
        elif message.content.startswith("!cv") and discord.opus.is_loaded():
            if message.author.voice.voice_channel is None:
                await client.send_message(message.channel, "⚠ Non sei in nessun canale!")
                return
            global voice_client
            voice_client = await client.join_voice_channel(message.author.voice.voice_channel)
            await client.send_message(message.channel, f"✅ Mi sono connesso in <#{message.author.voice.voice_channel.id}>.")
        elif message.content.startswith("!music"):
            if voice_client is None or not voice_client.is_connected():
                await client.send_message(message.channel, f"⚠ Il bot non è connesso in nessun canale.")
                return
            try:
                url = message.content.split(" ", 1)[1]
            except IndexError:
                await client.send_message(message.channel, "⚠️ Non hai specificato un URL.")
                return
            new_voice_player = await voice_client.create_ytdl_player(url)
            global voice_player
            if voice_player is not None:
                voice_player.stop()
            voice_player = new_voice_player
            voice_player.start()
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