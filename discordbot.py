import datetime

import discord
import discord.opus
import functools
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


async def find_user(user: discord.User):
    session = await loop.run_in_executor(None, db.Session)
    user = await loop.run_in_executor(None, session.query(db.Discord).filter_by(discord_id=user.id).first)
    return user


@client.event
async def on_message(message: discord.Message):
    if message.content.startswith("!register"):
        await client.send_typing(message.channel)
        session = await loop.run_in_executor(None, db.Session())
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
        session.close()
        await client.send_message(message.channel, "✅ Sincronizzazione completata!")
    elif message.content.startswith("!cv") and discord.opus.is_loaded():
        await client.send_typing(message.channel)
        if message.author.voice.voice_channel is None:
            await client.send_message(message.channel, "⚠ Non sei in nessun canale!")
            return
        global voice_client
        voice_client = await client.join_voice_channel(message.author.voice.voice_channel)
        await client.send_message(message.channel, f"✅ Mi sono connesso in <#{message.author.voice.voice_channel.id}>.")
    elif message.content.startswith("!play"):
        # Display typing status
        await client.send_typing(message.channel)
        # Check if the bot is connected to voice chat
        if voice_client is None or not voice_client.is_connected():
            await client.send_message(message.channel, f"⚠ Il bot non è connesso in nessun canale.")
            return
        # Get the URL from the message
        try:
            url = message.content.split(" ", 1)[1]
        except IndexError:
            await client.send_message(message.channel, "⚠️ Non hai specificato un URL.")
            return
        # Download the file and create a new voice player
        new_voice_player = await voice_client.create_ytdl_player(url, ytdl_options={
            "noplaylist": True
        })
        # Replace the old voice player with the new one
        global voice_player
        if voice_player is not None:
            voice_player.stop()
        voice_player = new_voice_player
        # Start playing the music
        voice_player.start()
        # Create the video rich embed
        embed = discord.Embed(type="rich",
                              title=voice_player.title,
                              url=voice_player.url,
                              colour=discord.Colour(13375518))
        embed.set_author(name=voice_player.uploader)
        embed.add_field(name="Durata", value=str(datetime.timedelta(seconds=voice_player.duration)), inline=False)
        if voice_player.views is not None:
            embed.add_field(name="Visualizzazioni", value="{:_}".format(voice_player.views).replace("_", " "))
        if voice_player.likes is not None:
            embed.add_field(name="Mi piace", value="{:_}".format(voice_player.likes).replace("_", " "))
        if voice_player.dislikes is not None:
            embed.add_field(name="Non mi piace", value="{:_}".format(voice_player.dislikes).replace("_", " "))
        # Send the embed in the chat channel where the command was sent
        await client.send_message(message.channel, f"▶️ In riproduzione:", embed=embed)
        # Find the message sender in the db
        user = await find_user(message.author)
        # Add the audio to the database
        await loop.run_in_executor(None, functools.partial(db.CVMusic.create_and_add, voice_player.title, user.royal_id))
    elif message.content.startswith("!pause"):
        await client.send_typing(message.channel)
        if voice_player is None:
            await client.send_message(message.channel, f"⚠ Nessun file audio sta venendo attualmente riprodotto.")
            return
        voice_player.pause()
        await client.send_message(message.channel, f"⏸ Riproduzione messa in pausa.")
    elif message.content.startswith("!resume"):
        await client.send_typing(message.channel)
        if voice_player is None:
            await client.send_message(message.channel, f"⚠ Nessun file audio sta venendo attualmente riprodotto.")
            return
        voice_player.resume()
        await client.send_message(message.channel, f"▶️ Riproduzione ripresa.")
    elif message.content.startswith("!stop"):
        await client.send_typing(message.channel)
        if voice_player is None:
            await client.send_message(message.channel, f"⚠ Nessun file audio sta venendo attualmente riprodotto.")
            return
        voice_player.stop()
        await client.send_message(message.channel, f"⏹ Riproduzione interrotta.")

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