import datetime
import random
import discord
import discord.opus
import discord.voice_client
import functools
import sys
import db
import errors
import youtube_dl
import concurrent.futures
import stagismo
import platform
import uuid
import typing

# Init the event loop
import asyncio
loop = asyncio.get_event_loop()

# Init the config reader
import configparser
config = configparser.ConfigParser()
config.read("config.ini")

class Video:
    def __init__(self):
        self.user = None
        self.filename = None
        self.ytdl_url = None

    @staticmethod
    async def init(user, filename=None, ytdl_url=None):
        if filename is None and ytdl_url is None:
            raise Exception("Filename or url must be specified")
        self = Video()
        discord_user = await find_user(user)
        self.user = discord_user.royal if discord_user is not None else None
        self.filename = filename
        self.ytdl_url = ytdl_url
        return self

    async def download(self) -> bool:
        # Don't download already existent files
        if self.filename is not None:
            return True
        file_id = uuid.uuid4()
        ytdl_args = {"noplaylist": True,
                     "format": "bestaudio",
                     "postprocessors": [{
                         "key": 'FFmpegExtractAudio',
                         "preferredcodec": 'opus'
                     }],
                     "outtmpl": f"opusfiles/{file_id}.opus"}
        if "youtu" in self.ytdl_url:
            ytdl_args["username"] = config["YouTube"]["username"]
            ytdl_args["password"] = config["YouTube"]["password"]
        # Download the video
        try:
            with youtube_dl.YoutubeDL(ytdl_args) as ytdl:
                await loop.run_in_executor(executor, functools.partial(ytdl.download, [self.ytdl_url]))
        except Exception as e:
            print(e)
            return False
        # Set the filename to the downloaded video
        self.filename = f"opusfiles/{file_id}.opus"
        return True

if __debug__:
    version = "Dev"
else:
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
if platform.system() == "Linux":
    discord.opus.load_opus("/usr/lib/x86_64-linux-gnu/libopus.so")
elif platform.system() == "Windows":
    discord.opus.load_opus("libopus-0.dll")

voice_client: typing.Optional[discord.VoiceClient] = None
voice_player: typing.Optional[discord.voice_client.StreamPlayer] = None
voice_queue: typing.List[Video] = []

# Init the executor
executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

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
        # If target is a single video
        video = await Video.init(user=message.author, ytdl_url=url)
        await client.send_message(message.channel, f"✅ Aggiunto alla coda: `{url}`")
        voice_queue.append(video)
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
        # If target is a single video
        video = await Video.init(user=message.author, ytdl_url=f"ytsearch:{text}")
        await client.send_message(message.channel, f"✅ Aggiunto alla coda: `ytsearch:{text}`")
        voice_queue.append(video)
    elif message.content.startswith("!file"):
        await client.send_typing(message.channel)
        # The bot should be in voice chat
        if voice_client is None:
            await client.send_message(message.channel, "⚠️ Non sono connesso alla cv!\n"
                                                       "Fammi entrare scrivendo `!cv` mentre sei in chat vocale.")
            return
        # Find the sent text
        try:
            text:str = message.content.split(" ", 1)[1]
        except IndexError:
            await client.send_message(message.channel, "⚠️ Non hai specificato il nome del file!\n"
                                                       "Sintassi corretta: `!file <nomefile>`")
            return
        # Ensure the filename ends with .opus
        if not text.endswith(".opus"):
            await client.send_message(message.channel, "⚠️ Il nome file specificato non è valido.")
            return
        # If target is a single video
        video = await Video.init(user=message.author, filename=text)
        await client.send_message(message.channel, f"✅ Aggiunto alla coda: `{text}`")
        voice_queue.append(video)
    elif message.content.startswith("!skip"):
        global voice_player
        voice_player.stop()
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
        if not len(voice_queue) > 1:
            await client.send_message(message.channel, f"⚠ Non ci sono video da annullare.")
            return
        video = voice_queue.pop()
        await client.send_message(message.channel, f"❌ L'ultimo video aggiunto alla playlist è stato rimosso.")
    elif message.content.startswith("!stop"):
        if voice_player is None:
            await client.send_message(message.channel, f"⚠ Non c'è nulla da interrompere!")
            return
        voice_queue = []
        voice_player.stop()
        voice_player = None
        await client.send_message(message.channel, f"⏹ Riproduzione interrotta e playlist svuotata.")
    #elif message.content.startswith("!np"):
    #    if voice_player is None or not voice_player.is_playing():
    #        await client.send_message(message.channel, f"ℹ Non c'è nulla in riproduzione al momento.")
    #        return
    #    await client.send_message(message.channel, f"▶️ Ora in riproduzione in <#{voice_client.channel.id}>:", embed=voice_playing.create_embed())
    #elif message.content.startswith("!queue"):
    #    if voice_player is None:
    #        await client.send_message(message.channel, f"ℹ Non c'è nulla in riproduzione al momento.")
    #        return
    #    to_send = ""
    #    to_send += f"0. {voice_playing.info['title'] if voice_playing.info['title'] is not None else '_Senza titolo_'} - <{voice_playing.info['webpage_url'] if voice_playing.info['webpage_url'] is not None else ''}>\n"
    #    for n, video in enumerate(voice_queue):
    #        to_send += f"{n+1}. {video.info['title'] if video.info['title'] is not None else '_Senza titolo_'} - <{video.info['webpage_url'] if video.info['webpage_url'] is not None else ''}>\n"
    #        if len(to_send) >= 2000:
    #            to_send = to_send[0:1997] + "..."
    #            break
    #    await client.send_message(message.channel, to_send)
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
    elif message.content.startswith("!smecds"):
        ds = random.sample(stagismo.listona, 1)[0]
        await client.send_message(message.channel, f"Secondo me, è colpa {ds}.", tts=True)
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
    global voice_client
    global voice_player
    global voice_queue
    while True:
        if voice_client is None:
            await asyncio.sleep(5)
            continue
        if voice_player is not None and not voice_player._end.is_set():
            await asyncio.sleep(1)
            continue
        if len(voice_queue) == 0:
            await client.change_presence()
            await asyncio.sleep(1)
            continue
        video = voice_queue.pop()
        if video.ytdl_url:
            await client.send_message(client.get_channel(config["Discord"]["main_channel"]), f"ℹ E' iniziato il download di `{video.ytdl_url}`.")
            success = await video.download()
            if not success:
                await client.send_message(client.get_channel(config["Discord"]["main_channel"]), f"⚠️ C'è stato un errore durante il download di `{video.ytdl_url}`")
                continue
        voice_player = voice_client.create_ffmpeg_player(video.filename)
        voice_player.start()
        await client.send_message(client.get_channel(config["Discord"]["main_channel"]), f"▶ Ora in riproduzione in <#{voice_client.channel.id}>:\n"
                                                 f"`{video.filename}`")
        await client.change_presence(game=discord.Game(name="YouTube", type=2))


def process(users_connection=None):
    print("Discordbot starting...")
    if users_connection is not None:
        asyncio.ensure_future(update_users_pipe(users_connection))
    asyncio.ensure_future(update_music_queue())
    client.on_error = on_error
    client.run(config["Discord"]["bot_token"])


if __name__ == "__main__":
    process()
