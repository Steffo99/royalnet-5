import random

import math

import db
import errors
from telegram import Bot, Update, Message
from telegram.ext import Updater, CommandHandler
from discord import Status as DiscordStatus

# Init the config reader
import configparser
config = configparser.ConfigParser()
config.read("config.ini")

discord_connection = None

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


def cmd_register(bot: Bot, update: Update):
    session = db.Session()
    try:
        username = update.message.text.split(" ", 1)[1]
    except IndexError:
        bot.send_message(update.message.chat.id, "⚠️ Non hai specificato un username!")
        return
    try:
        t = db.Telegram.create(session,
                               royal_username=username,
                               telegram_user=update.message.from_user)
    except errors.AlreadyExistingError:
        bot.send_message(update.message.chat.id, "⚠ Il tuo account Telegram è già collegato a un account RYG o l'account RYG che hai specificato è già collegato a un account Telegram.")
        return
    session.add(t)
    session.commit()
    bot.send_message(update.message.chat.id, "✅ Sincronizzazione completata!")
    session.close()


def cmd_discord(bot: Bot, update: Update):
    discord_connection.send("/cv")
    server_members = discord_connection.recv()
    message = ""
    for member in server_members:
        if member.status == DiscordStatus.offline and member.voice.voice_channel is None:
            continue
        if member.bot:
            continue
        # Online status emoji
        if member.status == DiscordStatus.online:
            message += "🔵 "
        elif member.status == DiscordStatus.idle:
            message += "⚫️ "
        elif member.status == DiscordStatus.dnd:
            message += "🔴 "
        elif member.status == DiscordStatus.offline:
            message += "⚪️ "
        # Nickname
        if member.nick is not None:
            message += member.nick
        else:
            message += member.name
        # Voice
        if member.voice.voice_channel is not None:
            # Voice status
            if member.voice.self_deaf:
                message += f" | 🔇 {member.voice.voice_channel.name}"
            elif member.voice.self_mute:
                message += f" | 🔈 {member.voice.voice_channel.name}"
            else:
                message += f" | 🔊 {member.voice.voice_channel.name}"
        # Game or stream
        if member.game is not None:
            if member.game.type == 0:
                message += f" | 🎮 {member.game.name}"
            elif member.game.type == 1:
                message += f" | 📡 [{member.game.name}]({member.game.url})"
        message += "\n"
    bot.send_message(update.message.chat.id, message, disable_web_page_preview=True, parse_mode="Markdown")


def cmd_cast(bot: Bot, update: Update):
    try:
        spell = update.message.text.split(" ", 1)[1]
    except IndexError:
        bot.send_message(update.message.chat.id, "⚠️ Non hai specificato nessun incantesimo!\n"
                                                 "Sintassi corretta: `/cast <nome_incantesimo>`")
        return
    # Open a new db session
    session = db.Session()
    # Find a target for the spell
    target = random.sample(session.query(db.Telegram).all(), 1)[0]
    # Close the session
    session.close()
    # Seed the rng with the spell name
    # so that spells always deal the same damage
    random.seed(spell)
    dmg_dice = random.randrange(1, 11)
    dmg_max = random.sample([4, 6, 8, 10, 12, 20, 100], 1)[0]
    dmg_mod = random.randrange(math.floor(-dmg_max / 5), math.ceil(dmg_max / 5) + 1)
    # Reseed the rng with a random value
    # so that the dice roll always deals a different damage
    random.seed()
    total = dmg_mod
    for dice in range(0, dmg_dice):
        total += random.randrange(1, dmg_max + 1)
    bot.send_message(update.message.chat.id, f"❇️ Ho lanciato {spell} su {target.username if target.username is not None else target.first_name} per {dmg_dice}d{dmg_max}{'+' if dmg_mod > 0 else ''}{str(dmg_mod) if dmg_mod != 0 else ''}={total if total > 0 else 0} danni!")


def process(arg_discord_connection):
    print("Telegrambot starting...")
    global discord_connection
    discord_connection = arg_discord_connection
    u = Updater(config["Telegram"]["bot_token"])
    u.dispatcher.add_handler(CommandHandler("register", cmd_register))
    u.dispatcher.add_handler(CommandHandler("discord", cmd_discord))
    u.dispatcher.add_handler(CommandHandler("cast", cmd_cast))
    u.start_polling()
    u.idle()