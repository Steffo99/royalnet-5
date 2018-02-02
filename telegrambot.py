import datetime
import random
import math
import db
import errors
import stagismo
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
        session.close()
        return
    try:
        t = db.Telegram.create(session,
                               royal_username=username,
                               telegram_user=update.message.from_user)
    except errors.AlreadyExistingError:
        bot.send_message(update.message.chat.id, "⚠ Il tuo account Telegram è già collegato a un account RYG o l'account RYG che hai specificato è già collegato a un account Telegram.")
        session.close()
        return
    session.add(t)
    session.commit()
    bot.send_message(update.message.chat.id, "✅ Sincronizzazione completata!")
    session.close()


def cmd_discord(bot: Bot, update: Update):
    if discord_connection is None:
        bot.send_message(update.message.chat.id, "⚠ Il bot non è sincronizzato con Discord al momento.")
        return
    discord_connection.send("/cv")
    server_members = discord_connection.recv()
    channels = {0:None}
    members_in_channels = {0:[]}
    message = ""
    # Find all the channels
    for member in server_members:
        if member.voice.voice_channel is not None:
            channel = members_in_channels.get(member.voice.voice_channel.id)
            if channel is None:
                members_in_channels[member.voice.voice_channel.id] = list()
                channel = members_in_channels[member.voice.voice_channel.id]
                channels[member.voice.voice_channel.id] = member.voice.voice_channel
            channel.append(member)
        else:
            members_in_channels[0].append(member)
    # Edit the message, sorted by channel
    for channel in channels:
        members_in_channels[channel].sort(key=lambda x: x.nick if x.nick is not None else x.name)
        if channel == 0:
            message += "Non in chat vocale:\n"
        else:
            message += f"In #{channels[channel].name}:\n"
        for member in members_in_channels[channel]:
            if member.status == DiscordStatus.offline and member.voice.voice_channel is None:
                continue
            # Online status emoji
            if member.bot:
                message += "🤖 "
            elif member.status == DiscordStatus.online:
                message += "🔵 "
            elif member.status == DiscordStatus.idle:
                message += "⚫️ "
            elif member.status == DiscordStatus.dnd:
                message += "🔴 "
            elif member.status == DiscordStatus.offline:
                message += "⚪️ "
            # Voice
            if channel != 0:
                # Voice status
                if member.voice.self_deaf:
                    message += f"🔇 "
                elif member.voice.self_mute:
                    message += f"🔈 "
                else:
                    message += f"🔊 "
            # Nickname
            if member.nick is not None:
                message += member.nick
            else:
                message += member.name
            # Game or stream
            if member.game is not None:
                if member.game.type == 0:
                    message += f" | 🎮 {member.game.name}"
                elif member.game.type == 1:
                    message += f" | 📡 [{member.game.name}]({member.game.url})"
                elif member.game.type == 2:
                    message += f" | 🎧 {member.game.name}"
                elif member.game.type == 3:
                    message += f" | 📺 {member.game.name}"
            message += "\n"
        message += "\n"
    bot.send_message(update.message.chat.id, message, disable_web_page_preview=True)


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


def cmd_color(bot: Bot, update: Update):
    bot.send_message(update.message.chat.id, "I am sorry, unknown error occured during working with your request, Admin were notified")


def cmd_smecds(bot: Bot, update: Update):
    ds = random.sample(stagismo.listona, 1)[0]
    bot.send_message(update.message.chat.id, f"Secondo me, è colpa {ds}.")


def cmd_ciaoruozi(bot: Bot, update: Update):
    if update.message.from_user.username.lstrip("@") == "MeStakes":
        bot.send_message(update.message.chat.id, "Ciao me!")
    else:
        bot.send_message(update.message.chat.id, "Ciao Ruozi!")


def cmd_ahnonlosoio(bot: Bot, update: Update):
    if update.message.reply_to_message is not None and update.message.reply_to_message.text in ["/ahnonlosoio", "/ahnonlosoio@royalgamesbot", "Ah, non lo so io!"]:
        bot.send_message(update.message.chat.id, "Ah, non lo so neppure io!")
    else:
        bot.send_message(update.message.chat.id, "Ah, non lo so io!")


def cmd_balurage(bot: Bot, update: Update):
    session = db.Session()
    try:
        user = session.query(db.Telegram).filter_by(telegram_id=update.message.from_user.id).one_or_none()
        if user is None:
            bot.send_message(update.message.chat.id, "⚠ Il tuo account Telegram non è registrato al RYGdb! Registrati con `/register@royalgamesbot <nomeutenteryg>`.")
            return
        try:
            reason = update.message.text.split(" ", 1)[1]
        except IndexError:
            reason = None
        br = db.BaluRage(royal_id=user.royal_id, reason=reason)
        session.add(br)
        session.commit()
        bot.send_message(update.message.chat.id, f"😡 Stai sfogando la tua ira sul bot!")
    except Exception as e:
        raise
    finally:
        session.close()


def cmd_diario(bot: Bot, update: Update):
    session = db.Session()
    try:
        user = session.query(db.Telegram).filter_by(telegram_id=update.message.from_user.id).one_or_none()
        if user is None:
            bot.send_message(update.message.chat.id, "⚠ Il tuo account Telegram non è registrato al RYGdb! Registrati con `/register@royalgamesbot <nomeutenteryg>`.")
            return
        try:
            text = update.message.text.split(" ", 1)[1]
            author = session.query(db.Telegram).filter_by(telegram_id=update.message.from_user.id).one_or_none()
            saver = author
        except IndexError:
            if update.message.reply_to_message is None:
                bot.send_message(update.message.chat.id, f"⚠ Non hai specificato cosa aggiungere al diario! Puoi rispondere `/diario@royalgamesbot` al messaggio che vuoi salvare nel diario oppure scrivere `/diario@royalgamesbot <messaggio>` per aggiungere quel messaggio nel diario.\n"
                                                         f"Se l'hai fatto, e continua a comparire questo errore, allora Telegram è stupido e non mi vuole far vedere il messaggio a cui hai risposto.")
                return
            text = update.message.reply_to_message.text
            author = session.query(db.Telegram).filter_by(telegram_id=update.message.reply_to_message.from_user.id).one_or_none()
            saver = session.query(db.Telegram).filter_by(telegram_id=update.message.from_user.id).one_or_none()
        if text is None:
            bot.send_message(update.message.chat.id, f"⚠ Il messaggio a cui hai risposto non contiene testo.")
            return
        diario = db.Diario(timestamp=datetime.datetime.now(),
                           saver=saver,
                           author=author,
                           text=text)
        session.add(diario)
        session.commit()
        bot.send_message(update.message.chat.id, f"✅ Aggiunto al diario!")
    except Exception:
        raise
    finally:
        session.close()


def process(arg_discord_connection):
    print("Telegrambot starting...")
    if arg_discord_connection is not None:
        global discord_connection
        discord_connection = arg_discord_connection
    u = Updater(config["Telegram"]["bot_token"])
    u.dispatcher.add_handler(CommandHandler("register", cmd_register))
    u.dispatcher.add_handler(CommandHandler("discord", cmd_discord))
    u.dispatcher.add_handler(CommandHandler("cv", cmd_discord))
    u.dispatcher.add_handler(CommandHandler("cast", cmd_cast))
    u.dispatcher.add_handler(CommandHandler("color", cmd_color))
    u.dispatcher.add_handler(CommandHandler("smecds", cmd_smecds))
    u.dispatcher.add_handler(CommandHandler("ciaoruozi", cmd_ciaoruozi))
    u.dispatcher.add_handler(CommandHandler("ahnonlosoio", cmd_ahnonlosoio))
    u.dispatcher.add_handler(CommandHandler("balurage", cmd_balurage))
    u.dispatcher.add_handler(CommandHandler("diario", cmd_diario))
    u.start_polling()
    u.idle()

if __name__ == "__main__":
    process(None)