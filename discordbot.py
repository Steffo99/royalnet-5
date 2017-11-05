import datetime
import discord
import discord.opus
import functools
import db
import errors
import youtube_dl

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
voice_queue = asyncio.Queue()


async def find_user(user: discord.User):
    session = await loop.run_in_executor(None, db.Session)
    user = await loop.run_in_executor(None, session.query(db.Discord).filter_by(discord_id=user.id).first)
    return user


def create_music_embed(ytdl_data: dict):
    embed = discord.Embed(type="rich",
                          title=ytdl_data['title'] if 'title' in ytdl_data else None,
                          url=ytdl_data['webpage_url'] if 'webpage_url' in ytdl_data else None,
                          colour=discord.Colour(13375518))
    # Uploader
    if "uploader" in ytdl_data and ytdl_data["uploader"] is not None:
        embed.set_author(name=ytdl_data["uploader"], url=ytdl_data["uploader_url"] if "uploader_url" in ytdl_data else None)
    # Thumbnail
    if "thumbnail" in ytdl_data:
        embed.set_thumbnail(url=ytdl_data["thumbnail"])
    # Duration
    embed.add_field(name="Durata", value=str(datetime.timedelta(seconds=ytdl_data["duration"])))
    # Views
    if "view_count" in ytdl_data and ytdl_data["view_count"] is not None:
        embed.add_field(name="Visualizzazioni", value="{:_}".format(ytdl_data["view_count"]).replace("_", " "))
    # Likes
    if "like_count" in ytdl_data and ytdl_data["like_count"] is not None:
        embed.add_field(name="Mi piace", value="{:_}".format(ytdl_data["like_count"]).replace("_", " "))
    # Dislikes
    if "dislike_count" in ytdl_data and ytdl_data["dislike_count"] is not None:
        embed.add_field(name="Non mi piace", value="{:_}".format(ytdl_data["dislike_count"]).replace("_", " "))
    return embed


@client.event
async def on_message(message: discord.Message):
    if message.content.startswith("!register"):
        await client.send_typing(message.channel)
        session = await loop.run_in_executor(None, db.Session())
        try:
            username = message.content.split(" ", 1)[1]
        except IndexError:
            await client.send_message(message.channel, "⚠️ Non hai specificato un username!\n"
                                                       "Sintassi corretta: `!register <username_ryg>`")
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
    elif message.content.startswith("!madd"):
        await client.send_typing(message.channel)
        # The bot should be in voice chat
        if voice_client is None:
            await client.send_message(message.channel, "⚠️ Non sono connesso alla cv!\n"
                                                       "Fammi entrare scrivendo `!cv` mentre sei in chat vocale.")
        # Find the sent url
        try:
            url = message.content.split(" ", 1)[1]
        except IndexError:
            await client.send_message(message.channel, "⚠️ Non hai specificato un url!\n"
                                                       "Sintassi corretta: `!madd <video>`")
            return
        # Se è una playlist, informa che potrebbe essere richiesto un po' di tempo
        if "playlist" in url:
            await client.send_message(message.channel, f"ℹ️ Hai inviato una playlist al bot.\n"
                                                       f"L'elaborazione potrebbe richiedere un po' di tempo.")
        # Extract the info from the url
        try:
            with youtube_dl.YoutubeDL({"quiet": True, "skip_download": True, "noplaylist": True, "format": "webm[abr>0]/bestaudio/best"}) as ytdl:
                info = await loop.run_in_executor(None, functools.partial(ytdl.extract_info, url))
        except youtube_dl.utils.DownloadError as e:
            if "is not a valid URL" in str(e):
                await client.send_message(message.channel, f"⚠️ Il link inserito non è valido.\n"
                                                           f"Se vuoi cercare un video su YouTube, usa `!msearch <query>`")
            return
        if "_type" not in info:
            # If target is a single video
            await client.send_message(message.channel, f"✅ Aggiunto alla coda:", embed=create_music_embed(info))
            voice_queue.put(info)
        elif info["_type"] == "playlist":
            # If target is a playlist
            if len(info["entries"]) < 20:
                for video in info["entries"]:
                    await client.send_message(message.channel, f"✅ Aggiunto alla coda:",
                                              embed=create_music_embed(video))
                    voice_queue.put(video)
            else:
                await client.send_message(message.channel, f"ℹ La playlist contiene {len(info['entries'])} video.\n"
                                                           f"Sei sicuro di volerli aggiungere alla coda?\n"
                                                           f"Rispondi **sì** o **no**.\n"
                                                           f"_(Il bot potrebbe crashare.)_")
                answer = await client.wait_for_message(timeout=60, author=message.author, channel=message.channel)
                if "sì" in answer.content.lower() or "si" in answer.content.lower():
                    for video in info["entries"]:
                        await client.send_message(message.channel, f"✅ Aggiunto alla coda:",
                                                  embed=create_music_embed(video))
                        voice_queue.put(video)
                elif "no" in answer.content.lower():
                    await client.send_message(message.channel, f"ℹ Operazione annullata.")
                    return
    elif message.content.startswith("!mstart"):
        await update_music_queue()
    elif message.content.startswith("!msearch"):
        raise NotImplementedError()
    elif message.content.startswith("!mskip"):
        raise NotImplementedError()
    elif message.content.startswith("!mpause"):
        raise NotImplementedError()
    elif message.content.startswith("!mresume"):
        raise NotImplementedError()
    elif message.content.startswith("!mcancel"):
        raise NotImplementedError()
    elif message.content.startswith("!mstop"):
        raise NotImplementedError()


async def update_users_pipe(users_connection):
    await client.wait_until_ready()
    while True:
        msg = await loop.run_in_executor(None, users_connection.recv)
        if msg == "/cv":
            discord_members = list(client.get_server(config["Discord"]["server_id"]).members)
            users_connection.send(discord_members)


async def update_music_queue():
    # Get the last video in the queue
    info = voice_queue.get()
    # Download the video
    with youtube_dl.YoutubeDL({"noplaylist": True,
                               "format": "bestaudio",
                               "postprocessors": [{
                                   "key": 'FFmpegExtractAudio',
                                   "preferredcodec": 'opus'
                               }],
                               "outtmpl": "music.%(ext)s"}) as ytdl:
        info = await loop.run_in_executor(None, functools.partial(ytdl.extract_info, info["webpage_url"]))
    # Play the video
    global voice_player
    voice_player = voice_client.create_ffmpeg_player(f"music.opus")
    voice_player.start()
    pass

def process(users_connection):
    print("Discordbot starting...")
    loop.create_task(update_users_pipe(users_connection))
    client.run(config["Discord"]["bot_token"])