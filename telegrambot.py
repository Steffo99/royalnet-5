import datetime
import random
import math
import db
import errors
import stagismo
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import telegram.error
from discord import Status as DiscordStatus
import subprocess
import os
import time

# Init the config reader
import configparser
config = configparser.ConfigParser()
config.read("config.ini")

discord_connection = None

# Find the latest git tag
if __debug__:
    version = "Dev"
    commit_msg = "_in sviluppo_"
else:
    # Find the latest git tag
    old_wd = os.getcwd()
    try:
        os.chdir(os.path.dirname(__file__))
        version = str(subprocess.check_output(["git", "describe", "--tags"]), encoding="utf8").strip()
        commit_msg = str(subprocess.check_output(["git", "log", "-1", "--pretty=%B"]), encoding="utf8").strip()
    except Exception:
        version = "❓"
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
        bot.send_message(update.message.chat.id, "⚠ Il tuo account Telegram è già collegato a un account RYG o"
                                                 " l'account RYG che hai specificato è già collegato a un account"
                                                 " Telegram.")
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
    except Exception:
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


def cmd_vote(bot: Bot, update: Update):
    session = db.Session()
    try:
        user = session.query(db.Telegram).filter_by(telegram_id=update.message.from_user.id).one_or_none()
        if user is None:
            bot.send_message(update.message.chat.id,
                             "⚠ Il tuo account Telegram non è registrato al RYGdb! Registrati con `/register@royalgamesbot <nomeutenteryg>`.")
            return
        try:
            _, mode, question = update.message.text.split(" ", 2)
        except IndexError:
            bot.send_message(update.message.chat.id,
                             "⚠ Non hai specificato tutti i parametri necessari!"
                             "Sintassi: `/vote@royalgamesbot <public|secret> <domanda>`")
            return
        if mode == "public":
            vote = db.VoteQuestion(question=question, anonymous=False)
        elif mode == "secret":
            vote = db.VoteQuestion(question=question, anonymous=True)
        else:
            bot.send_message(update.message.chat.id,
                             "⚠ Non hai specificato una modalità valida!"
                             "Sintassi: `/vote@royalgamesbot <public|secret> <domanda>`")
            return
        session.add(vote)
        session.flush()
        inline_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔵 Sì", callback_data="vote_yes")],
                                                [InlineKeyboardButton("🔴 No", callback_data="vote_no")],
                                                [InlineKeyboardButton("⚫️ Astieniti", callback_data="vote_abstain")]])
        message = bot.send_message(update.message.chat.id, vote.generate_text(session=session), reply_markup=inline_keyboard,
                                   parse_mode="HTML")
        vote.message_id = message.message_id
        session.commit()
    except Exception as e:
        raise
    finally:
        session.close()


def on_callback_query(bot: Bot, update: Update):
    if update.callback_query.data == "vote_yes":
        choice = db.VoteChoices.YES
        emoji = "🔵"
    elif update.callback_query.data == "vote_no":
        choice = db.VoteChoices.NO
        emoji = "🔴"
    elif update.callback_query.data == "vote_abstain":
        choice = db.VoteChoices.ABSTAIN
        emoji = "⚫️"
    else:
        raise NotImplementedError()
    if update.callback_query.data.startswith("vote_"):
        session = db.Session()
        try:
            user = session.query(db.Telegram).filter_by(telegram_id=update.callback_query.from_user.id).one_or_none()
            if user is None:
                bot.answer_callback_query(update.callback_query.id, show_alert=True,
                                          text="⚠ Il tuo account Telegram non è registrato al RYGdb!"
                                               " Registrati con `/register@royalgamesbot <nomeutenteryg>`.")
                return
            question = session.query(db.VoteQuestion).filter_by(message_id=update.callback_query.message.message_id).one()
            answer = session.query(db.VoteAnswer).filter_by(question=question, user=user).one_or_none()
            if answer is None:
                answer = db.VoteAnswer(question=question, choice=choice, user=user)
                session.add(answer)
            else:
                answer.choice = choice
            session.commit()
            bot.answer_callback_query(update.callback_query.id, text=f"Hai votato {emoji}.", cache_time=1)
            inline_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔵 Sì", callback_data="vote_yes")],
                                                    [InlineKeyboardButton("🔴 No", callback_data="vote_no")],
                                                    [InlineKeyboardButton("⚫️ Astieniti", callback_data="vote_abstain")]])
            bot.edit_message_text(message_id=update.callback_query.message.message_id, chat_id=update.callback_query.message.chat.id,
                                  text=question.generate_text(session), reply_markup=inline_keyboard,
                                  parse_mode="HTML")
        except Exception:
            raise
        finally:
            session.close()


def cmd_ban(bot: Bot, update: Update):
    if datetime.date.today() != datetime.date(2019, 4, 1):
        bot.send_message(update.message.chat.id, "⚠ Non è il giorno adatto per bannare persone!")
        return
    session = db.Session()
    try:
        last_bans = session.query(db.AprilFoolsBan).filter(db.AprilFoolsBan.datetime > (datetime.datetime.now() - datetime.timedelta(minutes=15))).all()
        if len(last_bans) > 0:
            bot.send_message(update.message.chat.id, "⚠ /ban è in cooldown.\n"
                                                     "Può essere usato solo 1 volta ogni 15 minuti!")
            return
        try:
            arg = update.message.text.split(" ", 1)[1]
        except IndexError:
            bot.send_message(update.message.chat.id, "⚠ Devi specificare un bersaglio!")
            return
        target_user = session.query(db.Telegram).filter_by(username=arg).one_or_none()
        if target_user is None:
            bot.send_message(update.message.chat.id, "⚠ Il bersaglio specificato non esiste nel RYGdb.\n"
                                                     "Le possibilità sono due: non è un membro RYG, "
                                                     "oppure non si è ancora registrato e va bannato manualmente.")
            return
        if int(target_user.telegram_id) == 25167391:
            bot.send_message(update.message.chat.id, "⚠ Il creatore della chat non può essere espulso.")
            return
        bannerino = db.AprilFoolsBan(from_user_id=update.message.from_user.id, to_user_id=target_user.telegram_id, datetime=datetime.datetime.now())
        session.add(bannerino)
        session.commit()
        bot.kick_chat_member(update.message.chat.id, target_user.telegram_id)
        bot.unban_chat_member(update.message.chat.id, target_user.telegram_id)
        try:
            bot.send_message(target_user.telegram_id, "https://t.me/joinchat/AYAGH0TEav8WcbPVfNe75A")
        except Exception:
            pass
        bot.send_message(update.message.chat.id, "🔨")
    except Exception as e:
        pass
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
    u.dispatcher.add_handler(CommandHandler("vote", cmd_vote))
    u.dispatcher.add_handler(CommandHandler("ban", cmd_ban))
    u.dispatcher.add_handler(CallbackQueryHandler(on_callback_query))
    u.bot.send_message(config["Telegram"]["main_group"],
                       f"ℹ Royal Bot avviato e pronto a ricevere comandi!\n"
                       f"Ultimo aggiornamento: `{version}: {commit_msg}`")
    while True:
        try:
            u.start_polling()
            u.idle()
        except telegram.error.TimedOut:
            print("Telegrambot timed out.")
            time.sleep(60)
            print("Telegrambot restarting...")

if __name__ == "__main__":
    process(None)