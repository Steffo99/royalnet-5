import datetime
import random
import math
import typing
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
import cast
import re

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
        bot.send_message(update.message.chat.id, "⚠ Il bot non è collegato a Discord al momento.")
        return
    discord_connection.send("get cv")
    server_members = discord_connection.recv()
    channels = {0: None}
    members_in_channels = {0: []}
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
        spell: str = update.message.text.split(" ", 1)[1]
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
    bot.send_message(update.message.chat.id, cast.cast(spell_name=spell,
                                                       target_name=target.username if target.username is not None
                                                       else target.first_name, platform="telegram"),
                     parse_mode="HTML")


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
                             "⚠ Il tuo account Telegram non è registrato al RYGdb!"
                             " Registrati con `/register@royalgamesbot <nomeutenteryg>`.")
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


def cmd_eat(bot: Bot, update: Update):
    try:
        food: str = update.message.text.split(" ", 1)[1].capitalize()
    except IndexError:
        bot.send_message(update.message.chat.id, "⚠️ Non hai specificato cosa mangiare!\n"
                                                 "Sintassi corretta: `/food <cibo>`")
        return
    if "tonnuooooooro" in food.lower():
        bot.send_message(update.message.chat.id, "👻 Il pesce che hai mangiato era posseduto.\n"
                                                 "Spooky!")
        return
    bot.send_message(update.message.chat.id, f"🍗 Hai mangiato {food}!")


def cmd_ship(bot: Bot, update: Update):
    try:
        _, name_one, name_two = update.message.text.split(" ", 2)
    except IndexError:
        bot.send_message(update.message.chat.id, "⚠️ Non hai specificato correttamente i due nomi!\n"
                                                 "Sintassi corretta: `/ship <nome> <nome>`")
        return
    name_one = name_one.lower()
    name_two = name_two.lower()
    part_one = re.search(r"^[A-Za-z][^aeiouAEIOU]*[aeiouAEIOU]?", name_one)
    part_two = re.search(r"[^aeiouAEIOU]*[aeiouAEIOU]?[A-Za-z]$", name_two)
    try:
        mixed = part_one.group(0) + part_two.group(0)
    except:
        bot.send_message(update.message.chat.id, "⚠ I nomi specificati non sono validi.\n"
                                                 "Riprova con dei nomi diversi!")
        return
    if part_one is None or part_two is None:
        bot.send_message(update.message.chat.id, "⚠ I nomi specificati non sono validi.\n"
                                                 "Riprova con dei nomi diversi!")
        return
    bot.send_message(update.message.chat.id, f"💕 {name_one.capitalize()} + {name_two.capitalize()} ="
                                             f" {mixed.capitalize()}")


def cmd_profile(bot: Bot, update: Update):
    session = db.Session()
    user = session.query(db.Telegram).filter_by(telegram_id=update.message.from_user.id).join(db.Royal).one_or_none()
    session.close()
    if user is None:
        bot.send_message(update.message.chat.id, "⚠ Non sei connesso a Royalnet!\n"
                                                 "Per registrarti, utilizza il comando /register.")
        return
    bot.send_message(update.message.chat.id, f"👤 [Profilo di {user.royal.username}]"
                                             f"(http://ryg.steffo.eu/profile/{user.royal.username})\n"
                                             f"Attualmente, hai **{user.royal.fiorygi}** fiorygi.",
                     parse_mode="Markdown")


def cmd_bridge(bot: Bot, update: Update):
    try:
        data = update.message.text.split(" ", 1)[1]
    except IndexError:
        bot.send_message(update.message.chat.id, "⚠ Non hai specificato un comando!\n"
                                                 "Sintassi corretta: `/bridge <comando> <argomenti>`")
    discord_connection.send(f"!{data}")
    result = discord_connection.recv()
    if result == "error":
        bot.send_message(update.message.chat.id, "⚠ Esecuzione del comando fallita.")
    if result == "success":
        bot.send_message(update.message.chat.id, "⏩ Comando eseguito su Discord.")


def cmd_wheel(bot: Bot, update: Update):
    """Perchè il gioco d'azzardo è bello e salutare."""
    session = db.Session()
    user = session.query(db.Telegram).filter_by(telegram_id=update.message.from_user.id).join(db.Royal).one_or_none()
    if user is None:
        bot.send_message(update.message.chat.id, "⚠ Non sei connesso a Royalnet!\n"
                                                 "Per registrarti, utilizza il comando /register.")
        session.close()
        return
    if user.royal.fiorygi < 1:
        bot.send_message(update.message.chat.id, "⚠ Non hai abbastanza fiorygi per girare la ruota!\n"
                                                 "Costa 1 fioryg.")
        session.close()
        return
    user.royal.fiorygi -= 1
    r = random.randrange(20)
    if r == 9:
        bot.send_message(update.message.chat.id, "☸️  La ruota della fortuna gira, e si ferma su x8!\n"
                                                 "Hai ottenuto 8 fiorygi!")
        user.royal.fiorygi += 8
    elif r == 8 or r == 7:
        bot.send_message(update.message.chat.id, "☸️  La ruota della fortuna gira, e si ferma su x4!\n"
                                                 "Hai ottenuto 4 fiorygi!")
        user.royal.fiorygi += 4
    else:
        bot.send_message(update.message.chat.id, "☸️  La ruota della fortuna gira, e si ferma su un segno strano.\n"
                                                 "|  ||\n"
                                                 "|| |_")
    session.commit()
    session.close()


def parse_timestring(timestring: str) -> typing.Union[datetime.timedelta, datetime.datetime]:
    # Unix time
    try:
        unix_timestamp = float(timestring)
        return datetime.datetime.fromtimestamp(unix_timestamp)
    except ValueError:
        pass
    # Dashed time
    try:
        split_date = timestring.split("-")
        now = datetime.datetime.now()
        if len(split_date) == 5:
            # yyyy-mm-dd-hh-mm
            return datetime.datetime(*split_date)
        elif len(split_date) == 4:
            return now.replace(month=int(split_date[0]),
                               day=int(split_date[1]),
                               hour=int(split_date[2]),
                               minute=int(split_date[3]))
        elif len(split_date) == 3:
            return now.replace(day=int(split_date[0]),
                               hour=int(split_date[1]),
                               minute=int(split_date[2]))
        elif len(split_date) == 2:
            return now.replace(hour=int(split_date[0]),
                               minute=int(split_date[1]))
    except (IndexError, ValueError):
        pass
    # Simple time from now
    try:
        if timestring.endswith("w"):
            return datetime.timedelta(weeks=float(timestring[:-1]))
        elif timestring.endswith("d"):
            return datetime.timedelta(days=float(timestring[:-1]))
        elif timestring.endswith("h"):
            return datetime.timedelta(hours=float(timestring[:-1]))
        elif timestring.endswith("m"):
            return datetime.timedelta(minutes=float(timestring[:-1]))
    except Exception:
        pass
    # Nothing found
    raise ValueError("Nothing was found.")


def cmd_newevent(bot: Bot, update: Update):
    try:
        _, timestring, name_desc = update.message.text.split(" ", 2)
    except IndexError:
        bot.send_message(update.message.chat.id, "⚠️ Sintassi del comando non valida.\n"
                                                 "Sintassi corretta:\n"
                                                 "```/newevent <timestamp|[[[anno-]mese-]giorno-]ore-minuti"
                                                 "|{numero}{w|d|h|m}> <nome>\n"
                                                 "[descrizione]```")
        return
    try:
        name, description = name_desc.split("\n", 1)
    except IndexError:
        name = name_desc
        description = None
    # Parse the timestring
    try:
        parsed_time = parse_timestring(timestring)
    except ValueError:
        bot.send_message(update.message.chat.id, "⚠ Non è stato possibile leggere la data.\n"
                                                 "Sintassi corretta:\n"
                                                 "```/newevent <timestamp|[[[anno-]mese-]giorno-]ore-minuti"
                                                 "|{numero}{w|d|h|m}> <nome>\n"
                                                 "[descrizione]```")
        return
    # Create the event
    session = db.Session()
    telegram_user = session.query(db.Telegram).filter_by(telegram_id=update.message.from_user.id).join(db.Royal).one_or_none()
    event = db.Event(author=telegram_user.royal,
                     name=name,
                     description=description,
                     time=datetime.datetime.fromtimestamp(0))
    # Set the time
    if isinstance(parsed_time, datetime.datetime):
        event.time = parsed_time
    else:
        event.time_left = parsed_time
    # Save the event
    session.add(event)
    session.commit()
    session.close()
    bot.send_message(update.message.chat.id, "✅ Evento aggiunto al Calendario Royal Games!")


def cmd_calendar(bot: Bot, update: Update):
    session = db.Session()
    next_events = session.query(db.Event).filter(db.Event.time > datetime.datetime.now()).order_by(db.Event.time).all()
    session.close()
    msg = "📆 Prossimi eventi\n"
    for event in next_events:
        if event.time_left.days >= 1:
            msg += event.time.strftime('%Y-%m-%d %H:%M')
        else:
            msg += f"{int(event.time_left.total_seconds() // 3600)}h" \
                   f" {int((event.time_left.total_seconds() % 3600) // 60)}m"
        msg += f" <b>{event.name}</b>\n"
    msg += '\nPer ulteriori dettagli, visita <a href="https://ryg.steffo.eu">Royalnet</a>'
    bot.send_message(update.message.chat.id, msg, parse_mode="HTML", disable_web_page_preview=True)


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
    u.dispatcher.add_handler(CommandHandler("eat", cmd_eat))
    u.dispatcher.add_handler(CommandHandler("ship", cmd_ship))
    u.dispatcher.add_handler(CommandHandler("profile", cmd_profile))
    u.dispatcher.add_handler(CommandHandler("bridge", cmd_bridge))
    u.dispatcher.add_handler(CommandHandler("wheel", cmd_wheel))
    u.dispatcher.add_handler(CommandHandler("newevent", cmd_newevent))
    u.dispatcher.add_handler(CommandHandler("calendar", cmd_calendar))
    u.dispatcher.add_handler(CallbackQueryHandler(on_callback_query))
    u.bot.send_message(config["Telegram"]["main_group"],
                       f"ℹ Royal Bot avviato e pronto a ricevere comandi!\n"
                       f"Ultimo aggiornamento: `{version}: {commit_msg}`",
                       parse_mode="Markdown", disable_notification=True)
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