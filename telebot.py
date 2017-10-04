from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler
import logging
from db import session, Royal, Telegram

# Init the config reader
import configparser
config = configparser.ConfigParser()
config.read("config.ini")

# Init the logger
logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s] %(asctime)s | %(message)s")

# Init the Telegram Bot
updater = Updater(token=config["Telegram"]["bot_token"])


def message_sync(bot: Bot, update: Update):
    tg_user = update.message.from_user
    db_user = session.query(Telegram).filter(Telegram.telegram_id == tg_user.id).first()
    if db_user is None:
        # Find the royals table record matching the command argument
        try:
            tg_royal = update.message.text.split(" ", 1)[1]
        except IndexError:
            bot.send_message(update.message.chat.id, "⚠️ Non hai specificato nessun username!")
            return
        db_royal = session.query(Royal).filter(Royal.username == tg_royal).first()
        if db_royal is None:
            bot.send_message(update.message.chat.id, "⚠️ L'username che hai specificato non è valido!")
            return
        # Create the new user and link it to the royals table
        db_user = Telegram(royal_id=db_royal.id,
                           telegram_id=tg_user.id,
                           first_name=tg_user.first_name,
                           last_name=tg_user.last_name,
                           username=tg_user.username)
        session.add(db_user)
        session.commit()
    else:
        # Update user data
        db_user.first_name = tg_user.first_name
        db_user.last_name = tg_user.last_name
        db_user.username = tg_user.username
        session.commit()
    bot.send_message(update.message.chat.id, "✅ Sincronizzazione completata!")


updater.dispatcher.add_handler(CommandHandler("sync", message_sync))
updater.start_polling()