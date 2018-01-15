import datetime
import random
import discord
import discord.opus
import functools
import sys
import db
import errors
import youtube_dl
import concurrent.futures

# Init the event loop
import asyncio
loop = asyncio.get_event_loop()

# Init the config reader
import configparser
config = configparser.ConfigParser()
config.read("config.ini")

# Find the latest git tag
import subprocess
import os
old_wd = os.getcwd()
try:
    os.chdir(os.path.dirname(__file__))
    version = str(subprocess.check_output(["git", "describe", "--tags"]), encoding="utf8").strip()
except:
    version = "v???"
finally:
    os.chdir(old_wd)

# Init the discord bot
client = discord.Client()
discord.opus.load_opus("libopus-0.dll")
voice_client = None
voice_player = None
voice_queue = []
voice_playing = None

# Init the executor
executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

class Video:
    def __init__(self):
        self.user = None
        self.info = None
        self.enqueued = None
        self.channel = None

    @staticmethod
    async def init(author, info, enqueued, channel):
        self = Video()
        discord_user = await find_user(author)
        self.user = discord_user.royal if discord_user is not None else None
        self.info = info
        self.enqueued = enqueued
        self.channel = channel
        return self
        
    def create_embed(self):
        embed = discord.Embed(type="rich",
                              title=self.info.get("title"),
                              url=self.info.get("webpage_url"),
                              colour=discord.Colour(13375518))
        # Uploader
        if self.info.get("uploader"):
            embed.set_author(name=self.info["uploader"],
                             url=self.info.get("uploader_url"))
        # Thumbnail
        if "thumbnail" in self.info:
            embed.set_thumbnail(url=self.info["thumbnail"])
        # Duration
        embed.add_field(name="Durata", value=str(datetime.timedelta(seconds=self.info["duration"])))
        # Views
        if "view_count" in self.info and self.info["view_count"] is not None:
            embed.add_field(name="Visualizzazioni", value="{:_}".format(self.info["view_count"]).replace("_", " "))
        # Likes
        if "like_count" in self.info and self.info["like_count"] is not None:
            embed.add_field(name="Mi piace", value="{:_}".format(self.info["like_count"]).replace("_", " "))
        # Dislikes
        if "dislike_count" in self.info and self.info["dislike_count"] is not None:
            embed.add_field(name="Non mi piace", value="{:_}".format(self.info["dislike_count"]).replace("_", " "))
        return embed

    async def download(self):
        try:
            with youtube_dl.YoutubeDL({"noplaylist": True,
                                       "format": "bestaudio",
                                       "postprocessors": [{
                                           "key": 'FFmpegExtractAudio',
                                           "preferredcodec": 'opus'
                                       }],
                                       "outtmpl": "music.%(ext)s",
                                       "quiet": True}) as ytdl:
                info = await loop.run_in_executor(executor, functools.partial(ytdl.extract_info, self.info["webpage_url"]))
        except Exception as e:
            client.send_message(self.channel, f"⚠ Errore durante il download del video:\n"
                                              f"```"
                                              f"{e}"
                                              f"```", embed=self.create_embed())


async def find_user(user: discord.User):
    session = await loop.run_in_executor(executor, db.Session)
    user = await loop.run_in_executor(executor, session.query(db.Discord).filter_by(discord_id=user.id).join(db.Royal).first)
    return user


async def on_error(event, *args, **kwargs):
    type, exception, traceback = sys.exc_info()
    try:
        await client.send_message(client.get_channel(config["Discord"]["main_channel"]), f"☢️ ERRORE CRITICO NELL'EVENTO `{event}`\n"
              f"Il bot si è chiuso e si dovrebbe riavviare entro qualche minuto.\n\n"
              f"Dettagli dell'errore:\n"
              f"```python\n"
              f"{repr(exception)}\n"
              f"```")
        await voice_client.disconnect()
        await client.change_presence(status=discord.Status.invisible)
        await client.close()
    except Exception as e:
        print("ERRORE CRITICO PIU' CRITICO:\n" + repr(e) + "\n" + repr(sys.exc_info()))
    loop.stop()
    os._exit(1)
    pass


@client.event
async def on_ready():
    await client.send_message(client.get_channel("368447084518572034"), f"ℹ Royal Bot {version} avviato e pronto a ricevere comandi!")
    await client.change_presence(game=None, status=discord.Status.online)


@client.event
async def on_message(message: discord.Message):
    global voice_queue
    global voice_player
    if message.content.startswith("!register"):
        await client.send_typing(message.channel)
        session = await loop.run_in_executor(executor, db.Session())
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
    elif message.content.startswith("!cv"):
        await client.send_typing(message.channel)
        if message.author.voice.voice_channel is None:
            await client.send_message(message.channel, "⚠ Non sei in nessun canale!")
            return
        global voice_client
        if voice_client is not None and voice_client.is_connected():
            await voice_client.move_to(message.author.voice.voice_channel)
        else:
            voice_client = await client.join_voice_channel(message.author.voice.voice_channel)
        await client.send_message(message.channel, f"✅ Mi sono connesso in <#{message.author.voice.voice_channel.id}>.")
    elif message.content.startswith("!play"):
        await client.send_typing(message.channel)
        # The bot should be in voice chat
        if voice_client is None:
            await client.send_message(message.channel, "⚠️ Non sono connesso alla cv!\n"
                                                       "Fammi entrare scrivendo `!cv` mentre sei in chat vocale.")
            return
        # Find the sent url
        try:
            url = message.content.split(" ", 1)[1]
        except IndexError:
            await client.send_message(message.channel, "⚠️ Non hai specificato un url!\n"
                                                       "Sintassi corretta: `!play <video>`")
            return
        # Se è una playlist, informa che potrebbe essere richiesto un po' di tempo
        if "playlist" in url:
            await client.send_message(message.channel, f"ℹ️ Hai inviato una playlist al bot.\n"
                                                       f"L'elaborazione potrebbe richiedere un po' di tempo.")
        # Extract the info from the url
        try:
            with youtube_dl.YoutubeDL({"quiet": True, "skip_download": True, "noplaylist": True, "format": "webm[abr>0]/bestaudio/best"}) as ytdl:
                info = await loop.run_in_executor(executor, functools.partial(ytdl.extract_info, url))
        except youtube_dl.utils.DownloadError as e:
            if "is not a valid URL" in str(e) or "Unsupported URL" in str(e):
                await client.send_message(message.channel, f"⚠️ Il link inserito non è valido.\n"
                                                           f"Se vuoi cercare un video su YouTube, usa `!search <query>`")
            else:
                await client.send_message(message.channel, f"⚠ Errore:\n"
                                                           f"```\n"
                                                           f"{e}"
                                                           f"```")
            return
        if "_type" not in info:
            # If target is a single video
            video = await Video.init(author=message.author, info=info, enqueued=datetime.datetime.now(), channel=message.channel)
            await client.send_message(message.channel, f"✅ Aggiunto alla coda:", embed=video.create_embed())
            voice_queue.append(video)
        elif info["_type"] == "playlist":
            # If target is a playlist
            if len(info["entries"]) < 20:
                for single_info in info["entries"]:
                    video = await Video.init(author=message.author, info=single_info, enqueued=datetime.datetime.now(), channel=message.channel)
                    await client.send_message(message.channel, f"✅ Aggiunto alla coda:", embed=video.create_embed())
                    voice_queue.append(video)
            else:
                await client.send_message(message.channel, f"ℹ La playlist contiene {len(info['entries'])} video.\n"
                                                           f"Sei sicuro di volerli aggiungere alla coda?\n"
                                                           f"Rispondi **sì** o **no**.\n"
                                                           f"_(Il bot potrebbe crashare.)_")
                answer = await client.wait_for_message(timeout=60, author=message.author, channel=message.channel)
                if "sì" in answer.content.lower() or "si" in answer.content.lower():
                    for single_info in info["entries"]:
                        video = await Video.init(author=message.author, info=single_info,
                                                 enqueued=datetime.datetime.now(), channel=message.channel)
                        await client.send_message(message.channel, f"✅ Aggiunto alla coda:", embed=video.create_embed())
                        voice_queue.append(video)
                elif "no" in answer.content.lower():
                    await client.send_message(message.channel, f"ℹ Operazione annullata.")
                    return
    elif message.content.startswith("!search"):
        await client.send_typing(message.channel)
        # The bot should be in voice chat
        if voice_client is None:
            await client.send_message(message.channel, "⚠️ Non sono connesso alla cv!\n"
                                                       "Fammi entrare scrivendo `!cv` mentre sei in chat vocale.")
            return
        # Find the sent text
        try:
            text = message.content.split(" ", 1)[1]
        except IndexError:
            await client.send_message(message.channel, "⚠️ Non hai specificato il titolo!\n"
                                                       "Sintassi corretta: `!search <titolo>`")
            return
        # Extract the info from the url
        try:
            with youtube_dl.YoutubeDL({"quiet": True, "skip_download": True, "noplaylist": True, "format": "webm[abr>0]/bestaudio/best"}) as ytdl:
                info = await loop.run_in_executor(executor, functools.partial(ytdl.extract_info, f"ytsearch:{text}"))
        except youtube_dl.utils.DownloadError as e:
            if "is not a valid URL" in str(e) or "Unsupported URL" in str(e):
                await client.send_message(message.channel, f"⚠️ Il video ottenuto dalla ricerca non è valido. Prova a cercare qualcos'altro...")
            return
        # If target is a single video
        video = await Video.init(author=message.author, info=info["entries"][0], enqueued=datetime.datetime.now(), channel=message.channel)
        await client.send_message(message.channel, f"✅ Aggiunto alla coda:", embed=video.create_embed())
        voice_queue.append(video)
    elif message.content.startswith("!skip"):
        global voice_player
        voice_player.stop()
        voice_player = None
        await client.send_message(message.channel, f"⏩ Video saltato.")
    elif message.content.startswith("!pause"):
        if voice_player is None or not voice_player.is_playing():
            await client.send_message(message.channel, f"⚠️ Non è in corso la riproduzione di un video, pertanto non c'è niente da pausare.")
            return
        voice_player.pause()
        await client.send_message(message.channel, f"⏸ Riproduzione messa in pausa.\n"
                                                   f"Riprendi con `!resume`.")
    elif message.content.startswith("!resume"):
        if voice_player is None or voice_player.is_playing():
            await client.send_message(message.channel, f"⚠️ Non c'è nulla in pausa da riprendere!")
            return
        voice_player.resume()
        await client.send_message(message.channel, f"▶️ Riproduzione ripresa.")
    elif message.content.startswith("!cancel"):
        try:
            video = voice_queue.pop()
        except IndexError:
            await client.send_message(message.channel, f"⚠ La playlist è vuota.")
            return
        await client.send_message(message.channel, f"❌ Rimosso dalla playlist:", embed=video.create_embed())
    elif message.content.startswith("!stop"):
        if voice_player is None:
            await client.send_message(message.channel, f"⚠ Non c'è nulla da interrompere!")
            return
        voice_queue = []
        voice_player.stop()
        voice_player = None
        await client.send_message(message.channel, f"⏹ Riproduzione interrotta e playlist svuotata.")
    elif message.content.startswith("!np"):
        if voice_player is None:
            await client.send_message(message.channel, f"ℹ Non c'è nulla in riproduzione al momento.")
            return
        voice_queue = []
        voice_player.stop()
        voice_player = None
        await client.send_message(message.channel, f"ℹ Ora in riproduzione in <#{voice_client.channel.id}>:", embed=voice_playing.create_embed())
    elif message.content.startswith("!queue"):
        if voice_player is None:
            await client.send_message(message.channel, f"ℹ Non c'è nulla in riproduzione al momento.")
            return
        to_send = ""
        to_send += f"0. {voice_playing.info['title'] if voice_playing.info['title'] is not None else '_Senza titolo_'} - <{voice_playing.info['webpage_url'] if voice_playing.info['webpage_url'] is not None else ''}>\n"
        for n, video in enumerate(voice_queue):
            to_send += f"{n+1}. {video.info['title'] if video.info['title'] is not None else '_Senza titolo_'} - <{video.info['webpage_url'] if video.info['webpage_url'] is not None else ''}>\n"
            if len(to_send) >= 2000:
                to_send = to_send[0:1997] + "..."
                break
        await client.send_message(message.channel, to_send)
    elif message.content.startswith("!cast"):
        try:
            spell = message.content.split(" ", 1)[1]
        except IndexError:
            await client.send_message("⚠️ Non hai specificato nessun incantesimo!\n"
                                      "Sintassi corretta: `!cast <nome_incantesimo>`")
            return
        target = random.sample(list(message.server.members), 1)[0]
        # Seed the rng with the spell name
        # so that spells always deal the same damage
        random.seed(spell)
        dmg_mod = random.randrange(-2, 3)
        dmg_dice = random.randrange(1, 4)
        dmg_max = random.sample([4, 6, 8, 10, 12, 20, 100], 1)[0]
        # Reseed the rng with a random value
        # so that the dice roll always deals a different damage
        random.seed()
        total = dmg_mod
        for dice in range(0, dmg_dice):
            total += random.randrange(1, dmg_max+1)
        await client.send_message(message.channel, f"❇️ Ho lanciato **{spell}** su **{target.nick if target.nick is not None else target.name}** per {dmg_dice}d{dmg_max}{'+' if dmg_mod > 0 else ''}{str(dmg_mod) if dmg_mod != 0 else ''}=**{total if total > 0 else 0}** danni!")
    elif __debug__ and message.content.startswith("!exception"):
        raise Exception("!exception was called")


async def update_users_pipe(users_connection):
    await client.wait_until_ready()
    while True:
        msg = await loop.run_in_executor(executor, users_connection.recv)
        if msg == "/cv":
            discord_members = list(client.get_server(config["Discord"]["server_id"]).members)
            users_connection.send(discord_members)


async def update_music_queue():
    await client.wait_until_ready()
    global voice_player
    global voice_playing
    while True:
        # Wait until there is nothing playing
        if voice_client is not None and voice_player is not None and (voice_player.is_playing() and not voice_player.is_done()):
            await asyncio.sleep(1)
            continue
        if len(voice_queue) == 0:
            if voice_playing is not None:
                # Set the playing status
                voice_playing = None
                await client.change_presence()
            await asyncio.sleep(1)
            continue
        # Get the last video in the queue
        video = voice_queue.pop(0)
        # Notify the chat of the download
        await client.send_message(video.channel, f"ℹ E' iniziato il download della prossima canzone.")
        # Download the video
        await video.download()
        # Play the video
        voice_player = voice_client.create_ffmpeg_player(f"music.opus")
        voice_player.start()
        # Notify the chat of the start
        await client.send_message(video.channel, f"▶ Ora in riproduzione in <#{voice_client.channel.id}>:", embed=video.create_embed())
        # Set the playing status
        voice_playing = video
        await client.change_presence(game=discord.Game(name=video.info.get("title"), type=2))


def process(users_connection=None):
    print("Discordbot starting...")
    if users_connection is not None:
        asyncio.ensure_future(update_users_pipe(users_connection))
    asyncio.ensure_future(update_music_queue())
    client.on_error = on_error
    client.run(config["Discord"]["bot_token"])


if __name__ == "__main__":
    process()