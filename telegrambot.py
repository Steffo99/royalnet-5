import db
import errors
from telegram import Bot, Update, Message
from telegram.ext import Updater, CommandHandler

# Init the config reader
import configparser
config = configparser.ConfigParser()
config.read("config.ini")

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

u = Updater(config["Telegram"]["bot_token"])
u.dispatcher.add_handler(CommandHandler("register", cmd_register))
u.start_polling()
try:
    u.idle()
except KeyboardInterrupt:
    pass