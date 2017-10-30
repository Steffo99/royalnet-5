import db
import errors
from telegram import Bot, Update, Message
from telegram.ext import Updater, CommandHandler
from discord import Status as DiscordStatus

# Init the config reader
import configparser
config = configparser.ConfigParser()
config.read("config.ini")

users_connection = None

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
    users_connection.send("/cv")
    server_members = users_connection.recv()
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


def process(discord_users_connection):
    print("Telegrambot starting...")
    global users_connection
    users_connection = discord_users_connection
    u = Updater(config["Telegram"]["bot_token"])
    u.dispatcher.add_handler(CommandHandler("register", cmd_register))
    u.dispatcher.add_handler(CommandHandler("discord", cmd_discord))
    u.start_polling()
    u.idle()