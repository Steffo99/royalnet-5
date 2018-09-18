import datetime
import random
import typing
import db
import errors
import stagismo
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import dice
import sys
import os
import cast
import re
import logging
import configparser
import markovify
import raven
import coloredlogs

# Markov model
try:
    with open("markovmodel.json") as file:
        model = markovify.Text.from_json(file.read())
except Exception:
    model = None

logging.getLogger().disabled = True
logger = logging.getLogger(__name__)
os.environ["COLOREDLOGS_LOG_FORMAT"] = "%(asctime)s %(levelname)s %(name)s %(message)s"
coloredlogs.install(level="DEBUG", logger=logger)

# Init the config reader
config = configparser.ConfigParser()
config.read("config.ini")

discord_connection = None

# Init the Sentry client
sentry = raven.Client(config["Sentry"]["token"],
                      release=raven.fetch_git_sha(os.path.dirname(__file__)),
                      install_logging_hook=False,
                      hook_libraries=[])


def catch_and_report(func: "function"):
    def new_func(bot: Bot, update: Update):
        # noinspection PyBroadException
        try:
            return func(bot, update)
        except Exception:
            logger.error(f"Critical error: {sys.exc_info()}")
            # noinspection PyBroadException
            try:
                bot.send_message(int(config["Telegram"]["main_group"]),
                                 "☢ **ERRORE CRITICO!** \n"
                                 f"Il bot ha ignorato il comando.\n"
                                 f"Una segnalazione di errore è stata automaticamente mandata a @Steffo.\n\n"
                                 f"Dettagli dell'errore:\n"
                                 f"```\n"
                                 f"{sys.exc_info()}\n"
                                 f"```", parse_mode="Markdown")
            except Exception:
                logger.error(f"Double critical error: {sys.exc_info()}")
            if not __debug__:
                sentry.user_context({
                    "id": update.effective_user.id,
                    "telegram": {
                        "username": update.effective_user.username,
                        "first_name": update.effective_user.first_name,
                        "last_name": update.effective_user.last_name
                    }
                })
                sentry.extra_context({
                    "update": update.to_dict()
                })
                sentry.captureException()
    return new_func


@catch_and_report
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


@catch_and_report
def cmd_discord(bot: Bot, update: Update):
    if discord_connection is None:
        bot.send_message(update.message.chat.id, "⚠ Il bot non è collegato a Discord al momento.")
        return
    discord_connection.send("get cv")
    message = discord_connection.recv()
    bot.send_message(update.message.chat.id, message, disable_web_page_preview=True)


@catch_and_report
def cmd_cast(bot: Bot, update: Update):
    try:
        spell: str = update.message.text.split(" ", 1)[1]
    except IndexError:
        bot.send_message(update.message.chat.id, "⚠️ Non hai specificato nessun incantesimo!\n"
                                                 "Sintassi corretta: `/cast <nome_incantesimo>`", parse_mode="Markdown")
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


@catch_and_report
def cmd_color(bot: Bot, update: Update):
    bot.send_message(update.message.chat.id, "I am sorry, unknown error occured during working with your request, Admin were notified")


@catch_and_report
def cmd_smecds(bot: Bot, update: Update):
    ds = random.sample(stagismo.listona, 1)[0]
    bot.send_message(update.message.chat.id, f"Secondo me, è colpa {ds}.")


@catch_and_report
def cmd_ciaoruozi(bot: Bot, update: Update):
    if update.message.from_user.username.lstrip("@") == "MeStakes":
        bot.send_message(update.message.chat.id, "Ciao me!")
    else:
        bot.send_message(update.message.chat.id, "Ciao Ruozi!")


@catch_and_report
def cmd_ahnonlosoio(bot: Bot, update: Update):
    if update.message.reply_to_message is not None and update.message.reply_to_message.text in ["/ahnonlosoio", "/ahnonlosoio@royalgamesbot", "Ah, non lo so io!"]:
        bot.send_message(update.message.chat.id, "Ah, non lo so neppure io!")
    else:
        bot.send_message(update.message.chat.id, "Ah, non lo so io!")


@catch_and_report
def cmd_balurage(bot: Bot, update: Update):
    session = db.Session()
    try:
        user = session.query(db.Telegram).filter_by(telegram_id=update.message.from_user.id).one_or_none()
        if user is None:
            bot.send_message(update.message.chat.id, "⚠ Il tuo account Telegram non è registrato al RYGdb! Registrati con `/register@royalgamesbot <nomeutenteryg>`.", parse_mode="Markdown")
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


@catch_and_report
def cmd_diario(bot: Bot, update: Update):
    session = db.Session()
    try:
        user = session.query(db.Telegram).filter_by(telegram_id=update.message.from_user.id).one_or_none()
        if user is None:
            bot.send_message(update.message.chat.id, "⚠ Il tuo account Telegram non è registrato al RYGdb!"
                                                     " Registrati con `/register@royalgamesbot <nomeutenteryg>`.",
                             parse_mode="Markdown")
            return
        try:
            text = update.message.text.split(" ", 1)[1]
            author = session.query(db.Telegram).filter_by(telegram_id=update.message.from_user.id).one_or_none()
            saver = author
        except IndexError:
            if update.message.reply_to_message is None:
                bot.send_message(update.message.chat.id, f"⚠ Non hai specificato cosa aggiungere al diario! Puoi rispondere `/diario@royalgamesbot` al messaggio che vuoi salvare nel diario oppure scrivere `/diario@royalgamesbot <messaggio>` per aggiungere quel messaggio nel diario.\n"
                                                         f"Se l'hai fatto, e continua a comparire questo errore, allora Telegram è stupido e non mi vuole far vedere il messaggio a cui hai risposto.", parse_mode="Markdown")
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


@catch_and_report
def cmd_vote(bot: Bot, update: Update):
    session = db.Session()
    try:
        user = session.query(db.Telegram).filter_by(telegram_id=update.message.from_user.id).one_or_none()
        if user is None:
            bot.send_message(update.message.chat.id,
                             "⚠ Il tuo account Telegram non è registrato al RYGdb!"
                             " Registrati con `/register@royalgamesbot <nomeutenteryg>`.", parse_mode="Markdown")
            return
        try:
            _, mode, question = update.message.text.split(" ", 2)
        except IndexError:
            bot.send_message(update.message.chat.id,
                             "⚠ Non hai specificato tutti i parametri necessari!"
                             "Sintassi: `/vote@royalgamesbot <public|secret> <domanda>`", parse_mode="Markdown")
            return
        if mode == "public":
            vote = db.VoteQuestion(question=question, anonymous=False)
        elif mode == "secret":
            vote = db.VoteQuestion(question=question, anonymous=True)
        else:
            bot.send_message(update.message.chat.id,
                             "⚠ Non hai specificato una modalità valida!"
                             "Sintassi: `/vote@royalgamesbot <public|secret> <domanda>`", parse_mode="Markdown")
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


@catch_and_report
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
                                               " Registrati con `/register@royalgamesbot <nomeutenteryg>`.",
                                          parse_mode="Markdown")
                return
            question = session.query(db.VoteQuestion).filter_by(message_id=update.callback_query.message.message_id).one()
            answer = session.query(db.VoteAnswer).filter_by(question=question, user=user).one_or_none()
            if answer is None:
                answer = db.VoteAnswer(question=question, choice=choice, user=user)
                session.add(answer)
                bot.answer_callback_query(update.callback_query.id, text=f"Hai votato {emoji}.", cache_time=1)
            elif answer.choice == choice:
                session.delete(answer)
                bot.answer_callback_query(update.callback_query.id, text=f"Hai ritratto il tuo voto.", cache_time=1)
            else:
                answer.choice = choice
                bot.answer_callback_query(update.callback_query.id, text=f"Hai cambiato il tuo voto in {emoji}.",
                                          cache_time=1)
            session.commit()
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


@catch_and_report
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


@catch_and_report
def cmd_eat(bot: Bot, update: Update):
    try:
        food: str = update.message.text.split(" ", 1)[1].capitalize()
    except IndexError:
        bot.send_message(update.message.chat.id, "⚠️ Non hai specificato cosa mangiare!\n"
                                                 "Sintassi corretta: `/eat <cibo>`", parse_mode="Markdown")
        return
    if "tonnuooooooro" in food.lower():
        bot.send_message(update.message.chat.id, "👻 Il pesce che hai mangiato era posseduto.\n"
                                                 "Spooky!")
        return
    bot.send_message(update.message.chat.id, f"🍗 Hai mangiato {food}!")


@catch_and_report
def cmd_ship(bot: Bot, update: Update):
    try:
        _, name_one, name_two = update.message.text.split(" ", 2)
    except IndexError:
        bot.send_message(update.message.chat.id, "⚠️ Non hai specificato correttamente i due nomi!\n"
                                                 "Sintassi corretta: `/ship <nome> <nome>`", parse_mode="Markdown")
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


@catch_and_report
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


@catch_and_report
def cmd_bridge(bot: Bot, update: Update):
    try:
        data = update.message.text.split(" ", 1)[1]
    except IndexError:
        bot.send_message(update.message.chat.id, "⚠ Non hai specificato un comando!\n"
                                                 "Sintassi corretta: `/bridge <comando> <argomenti>`", parse_mode="Markdown")
    discord_connection.send(f"!{data}")
    result = discord_connection.recv()
    if result == "error":
        bot.send_message(update.message.chat.id, "⚠ Il comando specificato non esiste.")
    if result == "success":
        bot.send_message(update.message.chat.id, "⏩ Comando eseguito su Discord.")


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
            return datetime.datetime(year=int(split_date[0]),
                                     month=int(split_date[1]),
                                     day=int(split_date[2]),
                                     hour=int(split_date[3]),
                                     minute=int(split_date[4]))
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


@catch_and_report
def cmd_newevent(bot: Bot, update: Update):
    try:
        _, timestring, name_desc = update.message.text.split(" ", 2)
    except ValueError:
        bot.send_message(update.message.chat.id, "⚠️ Sintassi del comando non valida.\n"
                                                 "Sintassi corretta:\n"
                                                 "```/newevent <timestamp|[[[anno-]mese-]giorno-]ore-minuti"
                                                 "|{numero}{w|d|h|m}> <nome>\n"
                                                 "[descrizione]```", parse_mode="Markdown")
        return
    try:
        name, description = name_desc.split("\n", 1)
    except ValueError:
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
                                                 "[descrizione]```", parse_mode="Markdown")
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


@catch_and_report
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


@catch_and_report
def cmd_markov(bot: Bot, update: Update):
    if model is None:
        bot.send_message(update.message.chat.id, "⚠️ Il modello Markov non è disponibile.")
        return
    try:
        _, first_word = update.message.text.split(" ", 1)
    except ValueError:
        sentence = model.make_sentence(tries=1000)
        if sentence is None:
            bot.send_message(update.message.chat.id, "⚠ Complimenti! Hai vinto la lotteria di Markov!\n"
                                                     "O forse l'hai persa.\n"
                                                     "Non sono riuscito a generare una frase, riprova.")
            return
        bot.send_message(update.message.chat.id, sentence)
    else:
        sentence = model.make_sentence_with_start(first_word, tries=1000)
        if sentence is None:
            bot.send_message(update.message.chat.id, "⚠ Non è stato possibile generare frasi partendo da questa"
                                                     " parola.")
            return
        bot.send_message(update.message.chat.id, sentence)


@catch_and_report
def cmd_roll(bot: Bot, update: Update):
    dice_string = update.message.text.split(" ", 1)[1]
    try:
        result = dice.roll(f"{dice_string}t")
    except dice.DiceBaseException:
        bot.send_message(update.message.chat.id, "⚠ Il tiro dei dadi è fallito. Controlla la sintassi!")
        return
    bot.send_message(update.message.chat.id, f"🎲 {result}")


@catch_and_report
def cmd_exception(bot: Bot, update: Update):
    if __debug__:
        raise Exception("/exception was called")


def process(arg_discord_connection):
    if arg_discord_connection is not None:
        global discord_connection
        discord_connection = arg_discord_connection
    logger.info("Creating updater...")
    u = Updater(config["Telegram"]["bot_token"])
    logger.info("Registering handlers...")
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
    u.dispatcher.add_handler(CommandHandler("newevent", cmd_newevent))
    u.dispatcher.add_handler(CommandHandler("calendar", cmd_calendar))
    u.dispatcher.add_handler(CommandHandler("markov", cmd_markov))
    u.dispatcher.add_handler(CommandHandler("roll", cmd_roll))
    u.dispatcher.add_handler(CommandHandler("r", cmd_roll))
    if __debug__:
        u.dispatcher.add_handler(CommandHandler("exception", cmd_exception))
    u.dispatcher.add_handler(CallbackQueryHandler(on_callback_query))
    logger.info("Handlers registered.")
    u.start_polling()
    logger.info("Polling started.")
    u.idle()


if __name__ == "__main__":
    process(None)
