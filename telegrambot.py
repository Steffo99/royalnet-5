import datetime
import random
import typing
import db
import errors
import stagismo
from sqlalchemy.sql import text
# python-telegram-bot has a different name
# noinspection PyPackageRequirements
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton
# noinspection PyPackageRequirements
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram.error import TimedOut, Unauthorized
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
import strings
s = strings.safely_format_string

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
        except TimedOut:
            logger.warning(f"Telegram timed out in {update}")
        except Exception:
            if __debug__:
                raise
            logger.error(f"Critical error: {sys.exc_info()}")
            # noinspection PyBroadException
            try:
                bot.send_message(int(config["Telegram"]["main_group"]),
                                 s(strings.TELEGRAM.ERRORS.CRITICAL_ERROR, exc_info=sys.exc_info()),
                                 parse_mode="HTML")
            except Exception:
                logger.error(f"Double critical error: {sys.exc_info()}")
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
def cmd_ping(bot: Bot, update: Update):
    bot.send_message(update.message.chat.id, s(strings.PONG))


@catch_and_report
def cmd_register(bot: Bot, update: Update):
    session = db.Session()
    try:
        try:
            username = update.message.text.split(" ", 1)[1]
        except IndexError:
            bot.send_message(update.message.chat.id, s(strings.LINKING.ERRORS.INVALID_SYNTAX),
                             parse_mode="HTML")
            session.close()
            return
        try:
            t = db.Telegram.create(session,
                                   royal_username=username,
                                   telegram_user=update.message.from_user)
        except errors.NotFoundError:
            bot.send_message(update.message.chat.id, s(strings.LINKING.ERRORS.NOT_FOUND),
                             parse_mode="HTML")
            session.close()
            return
        except errors.AlreadyExistingError:
            bot.send_message(update.message.chat.id, s(strings.LINKING.ERRORS.ALREADY_EXISTING),
                             parse_mode="HTML")
            session.close()
            return
        session.add(t)
        session.commit()
        bot.send_message(update.message.chat.id, s(strings.LINKING.SUCCESSFUL),
                         parse_mode="HTML")
    finally:
        session.close()


@catch_and_report
def cmd_discord(bot: Bot, update: Update):
    if discord_connection is None:
        bot.send_message(update.message.chat.id, "⚠ Il bot non è collegato a Discord al momento.")
        return
    # dirty hack as usual
    if update.message.text.endswith("full"):
        discord_connection.send("get cv full")
    else:
        discord_connection.send("get cv")
    message = discord_connection.recv()
    bot.send_message(update.message.chat.id, message, disable_web_page_preview=True, parse_mode="HTML")


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
    # END
    bot.send_message(update.message.chat.id, cast.cast(spell_name=spell,
                                                       target_name=target.username if target.username is not None
                                                       else target.first_name, platform="telegram"),
                     parse_mode="HTML")


@catch_and_report
def cmd_color(bot: Bot, update: Update):
    bot.send_message(update.message.chat.id, "I am sorry, unknown error occured during working with your request,"
                                             " Admin were notified")


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
    if update.message.reply_to_message is not None and update.message.reply_to_message.text in [
        "/ahnonlosoio", "/ahnonlosoio@royalgamesbot", "Ah, non lo so io!", "Ah, non lo so neppure io!"
    ]:
        bot.send_message(update.message.chat.id, "Ah, non lo so neppure io!")
    else:
        bot.send_message(update.message.chat.id, "Ah, non lo so io!")


@catch_and_report
def cmd_balurage(bot: Bot, update: Update):
    session = db.Session()
    try:
        user = session.query(db.Telegram).filter_by(telegram_id=update.message.from_user.id).one_or_none()
        if user is None:
            bot.send_message(update.message.chat.id,
                             "⚠ Il tuo account Telegram non è registrato al RYGdb!\n\n"
                             "Registrati con `/register@royalgamesbot <nomeutenteryg>`.",
                             parse_mode="Markdown")
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
                bot.send_message(update.message.chat.id,
                                 f"⚠ Non hai specificato cosa aggiungere al diario!\n\n"
                                 f"Puoi rispondere `/diario@royalgamesbot` al messaggio che vuoi salvare nel diario"
                                 f" oppure scrivere `/diario@royalgamesbot <messaggio>`"
                                 f" per aggiungere quel messaggio nel diario.",
                                 parse_mode="Markdown")
                return
            text = update.message.reply_to_message.text
            author = session.query(db.Telegram)\
                            .filter_by(telegram_id=update.message.reply_to_message.from_user.id)\
                            .one_or_none()
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
        bot.send_message(update.message.chat.id,
                         f"✅ Riga [#{diario.id}](https://ryg.steffo.eu/diario#entry-{diario.id}) aggiunta al diario!",
                         parse_mode="Markdown", disable_web_page_preview=True)
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
        message = bot.send_message(update.message.chat.id, vote.generate_text(session=session),
                                   reply_markup=inline_keyboard,
                                   parse_mode="HTML")
        vote.message_id = message.message_id
        session.commit()
    finally:
        session.close()


@catch_and_report
def cmd_cerca(bot: Bot, update: Update):
    session = db.Session()
    try:
        try:
            queryText = update.message.text.split(" ", 1)[1]
        except IndexError:
            bot.send_message(update.message.chat.id, s(strings.DIARIO_SEARCH.ERRORS.INVALID_SYNTAX))
            return
        queryText = queryText.replace('%', '\\%').replace('_', '\\_')
        entries = session.query(db.Diario).filter(text(f"text ~* '(?:[^\w\d]+{queryText}[^\w\d]+|^{queryText}[^\w\d]+|^{queryText}$|[^\w\d]+{queryText}$)'")).order_by(db.Diario.id).all()
        cerca_message(bot, update, queryText, entries)
    finally:
        session.close()

def cerca_message (bot: Bot, update: Update, queryText, entries):
    msg = f"Risultati della ricerca di {queryText}:\n"
    for entry in entries[:5]:
        msg += f'<a href="https://ryg.steffo.eu/diario#entry-{entry.id}">#{entry.id}</a> di {entry.author or "Anonimo"}\n{entry.text}\n\n'
        if len(entries) > 5:
            msg += "I termini comapiono anche nelle righe:\n"
            for entry in entries[5:]:
                msg += f'<a href="https://ryg.steffo.eu/diario#entry-{entry.id}">#{entry.id}</a> '
    bot.send_message(update.message.chat.id, msg, parse_mode="HTML")

@catch_and_report
def cmd_mm(bot: Bot, update: Update):
    session = db.Session()
    try:
        user = session.query(db.Telegram).filter_by(telegram_id=update.message.from_user.id).one_or_none()
        if user is None:
            bot.send_message(update.message.chat.id, s(strings.TELEGRAM.ERRORS.TELEGRAM_NOT_LINKED), parse_mode="Markdown")
            return
        match = re.match(r"/(?:mm|matchmaking)(?:@royalgamesbot)?(?: (?:([0-9]+)-)?([0-9]+))? (?:per )?([A-Za-z0-9!\-_\. ]+)(?:.*\n(.+))?",
                         update.message.text)
        if match is None:
            bot.send_message(update.message.chat.id,
                             "")
            return
        min_players, max_players, match_name, match_desc = match.group(1, 2, 3, 4)
        db_match = db.Match(timestamp=datetime.datetime.now(),
                            match_title=match_name,
                            match_desc=match_desc,
                            min_players=min_players,
                            max_players=max_players,
                            creator=user)
        session.add(db_match)
        session.flush()
        inline_keyboard = InlineKeyboardMarkup([([InlineKeyboardButton(s(strings.MATCHMAKING.BUTTONS[key]),
                                                                       callback_data=key)])
                                                for key in strings.MATCHMAKING.BUTTONS])
        message = bot.send_message(config["Telegram"]["announcement_group"], db_match.generate_text(session=session),
                                   parse_mode="HTML",
                                   reply_markup=inline_keyboard)
        db_match.message_id = message.message_id
        session.commit()
    finally:
        session.close()


@catch_and_report
def on_callback_query(bot: Bot, update: Update):
    if update.callback_query.data.startswith("vote_"):
        if update.callback_query.data == "vote_yes":
            status = db.VoteChoices.YES
            emoji = "🔵"
        elif update.callback_query.data == "vote_no":
            status = db.VoteChoices.NO
            emoji = "🔴"
        elif update.callback_query.data == "vote_abstain":
            status = db.VoteChoices.ABSTAIN
            emoji = "⚫️"
        else:
            raise NotImplementedError()
        session = db.Session()
        try:
            user = session.query(db.Telegram).filter_by(telegram_id=update.callback_query.from_user.id).one_or_none()
            if user is None:
                bot.answer_callback_query(update.callback_query.id, show_alert=True,
                                          text=s(strings.TELEGRAM.ERRORS.TELEGRAM_NOT_LINKED),
                                          parse_mode="Markdown")
                return
            question = session.query(db.VoteQuestion)\
                              .filter_by(message_id=update.callback_query.message.message_id)\
                              .one()
            answer = session.query(db.VoteAnswer).filter_by(question=question, user=user).one_or_none()
            if answer is None:
                answer = db.VoteAnswer(question=question, choice=status, user=user)
                session.add(answer)
                bot.answer_callback_query(update.callback_query.id, text=f"Hai votato {emoji}.", cache_time=1)
            elif answer.choice == status:
                session.delete(answer)
                bot.answer_callback_query(update.callback_query.id, text=f"Hai ritratto il tuo voto.", cache_time=1)
            else:
                answer.choice = status
                bot.answer_callback_query(update.callback_query.id, text=f"Hai cambiato il tuo voto in {emoji}.",
                                          cache_time=1)
            session.commit()
            inline_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔵 Sì",
                                                                          callback_data="vote_yes")],
                                                    [InlineKeyboardButton("🔴 No",
                                                                          callback_data="vote_no")],
                                                    [InlineKeyboardButton("⚫️ Astieniti",
                                                                          callback_data="vote_abstain")]])
            bot.edit_message_text(message_id=update.callback_query.message.message_id,
                                  chat_id=update.callback_query.message.chat.id,
                                  text=question.generate_text(session),
                                  reply_markup=inline_keyboard,
                                  parse_mode="HTML")
        finally:
            session.close()
    elif update.callback_query.data.startswith("match_"):
        session = db.Session()
        try:
            user = session.query(db.Telegram).filter_by(telegram_id=update.callback_query.from_user.id).one_or_none()
            if user is None:
                bot.answer_callback_query(update.callback_query.id,
                                          show_alert=True,
                                          text=strings.TELEGRAM.ERRORS.TELEGRAM_NOT_LINKED,
                                          parse_mode="Markdown")
                return
            match = session.query(db.Match).filter_by(message_id=update.callback_query.message.message_id).one()
            if update.callback_query.data == "match_close":
                if match.creator != user:
                    bot.answer_callback_query(update.callback_query.id,
                                              show_alert=True,
                                              text=strings.MATCHMAKING.ERRORS.NOT_ADMIN)
                    return
                match.closed = True
                failed_send = []
                for player in match.players:
                    if player.status >= 1:
                        try:
                            bot.send_message(player.user.telegram_id,
                                             s(strings.MATCHMAKING.GAME_START[player.status],
                                               **match.format_dict()),
                                             parse_mode="HTML")
                        except Unauthorized:
                            failed_send.append(player)
                if failed_send:
                    for player in failed_send:
                        bot.send_message(int(config["Telegram"]["main_group"]),
                                         s(strings.MATCHMAKING.ERRORS.UNAUTHORIZED, mention=player.user.mention()))
            elif update.callback_query.data == "match_cancel":
                if not (match.creator == user or user.telegram_id == 25167391):
                    bot.answer_callback_query(update.callback_query.id,
                                              show_alert=True,
                                              text=strings.MATCHMAKING.ERRORS.NOT_ADMIN)
                    return
                match.closed = True
            status = {
                "match_ready": db.MatchmakingStatus.READY,
                "match_wait_for_me": db.MatchmakingStatus.WAIT_FOR_ME,
                "match_someone_else": db.MatchmakingStatus.SOMEONE_ELSE,
                "match_maybe": db.MatchmakingStatus.MAYBE,
                "match_ignore": db.MatchmakingStatus.IGNORED,
                "match_close": None,
                "match_cancel": None,
            }.get(update.callback_query.data)
            if status:
                if match.closed:
                    bot.answer_callback_query(update.callback_query.id,
                                              show_alert=True,
                                              text=strings.MATCHMAKING.ERRORS.MATCH_CLOSED)
                    return
                player = session.query(db.MatchPartecipation).filter_by(match=match, user=user).one_or_none()
                if player is None:
                    player = db.MatchPartecipation(match=match, status=status.value, user=user)
                    session.add(player)
                else:
                    player.status = status.value
            session.commit()
            bot.answer_callback_query(update.callback_query.id,
                                      text=strings.MATCHMAKING.TICKER_TEXT[update.callback_query.data],
                                      cache_time=1)
            if not match.closed:
                inline_keyboard = InlineKeyboardMarkup([([InlineKeyboardButton(strings.MATCHMAKING.BUTTONS[key],
                                                                               callback_data=key)])
                                                        for key in strings.MATCHMAKING.BUTTONS])
            else:
                inline_keyboard = None
            bot.edit_message_text(message_id=update.callback_query.message.message_id,
                                  chat_id=config["Telegram"]["announcement_group"],
                                  text=match.generate_text(session),
                                  reply_markup=inline_keyboard,
                                  parse_mode="HTML")
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
    except ValueError:
        bot.send_message(update.message.chat.id, "⚠️ Non hai specificato correttamente i due nomi!\n"
                                                 "Sintassi corretta: `/ship <nome> <nome>`", parse_mode="Markdown")
        return
    name_one = name_one.lower()
    name_two = name_two.lower()
    part_one = re.search(r"^[A-Za-z][^aeiouAEIOU]*[aeiouAEIOU]?", name_one)
    part_two = re.search(r"[^aeiouAEIOU]*[aeiouAEIOU]?[A-Za-z]$", name_two)
    try:
        mixed = part_one.group(0) + part_two.group(0)
    except Exception:
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
        bot.send_message(update.message.chat.id,
                         "⚠ Non hai specificato un comando!\n"
                         "Sintassi corretta: `/bridge <comando> <argomenti>`",
                         parse_mode="Markdown")
        return
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
        if parsed_time < datetime.datetime.now():
            raise errors.PastDateError()
    except ValueError:
        bot.send_message(update.message.chat.id, "⚠ Non è stato possibile leggere la data.\n"
                                                 "Sintassi corretta:\n"
                                                 "```/newevent <timestamp|[[[anno-]mese-]giorno-]ore-minuti"
                                                 "|{numero}{w|d|h|m}> <nome>\n"
                                                 "[descrizione]```", parse_mode="Markdown")
        return
    except errors.PastDateError:
        bot.send_message(update.message.chat.id, "⚠ La data inserita è una data passata.\n"
                                                 "per favore inserisci una data futura.\n", parse_mode="Markdown")
        return
    # Create the event
    session = db.Session()
    telegram_user = session.query(db.Telegram)\
                           .filter_by(telegram_id=update.message.from_user.id)\
                           .join(db.Royal)\
                           .one_or_none()
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
        bot.send_message(update.message.chat.id, strings.MARKOV.ERRORS.NO_MODEL)
        return
    try:
        first_word = update.message.text.split(" ")[1]
    except IndexError:
        # Any word
        sentence = model.make_sentence(tries=1000)
        if sentence is None:
            bot.send_message(update.message.chat.id, strings.MARKOV.ERRORS.GENERATION_FAILED)
            return
        bot.send_message(update.message.chat.id, sentence)
        return
    # Specific word
    try:
        sentence = model.make_sentence_with_start(first_word, tries=1000)
    except KeyError:
        bot.send_message(update.message.chat.id, strings.MARKOV.ERRORS.MISSING_WORD)
        return
    if sentence is None:
        bot.send_message(update.message.chat.id, strings.MARKOV.ERRORS.SPECIFIC_WORD_FAILED)
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


def process(arg_discord_connection):
    if arg_discord_connection is not None:
        global discord_connection
        discord_connection = arg_discord_connection
    logger.info("Creating updater...")
    u = Updater(config["Telegram"]["bot_token"])
    logger.info("Registering handlers...")
    u.dispatcher.add_handler(CommandHandler("ping", cmd_ping))
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
    u.dispatcher.add_handler(CommandHandler("spaggia", cmd_diario))
    u.dispatcher.add_handler(CommandHandler("vote", cmd_vote))
    u.dispatcher.add_handler(CommandHandler("eat", cmd_eat))
    u.dispatcher.add_handler(CommandHandler("ship", cmd_ship))
    u.dispatcher.add_handler(CommandHandler("profile", cmd_profile))
    u.dispatcher.add_handler(CommandHandler("bridge", cmd_bridge))
    u.dispatcher.add_handler(CommandHandler("newevent", cmd_newevent))
    u.dispatcher.add_handler(CommandHandler("calendar", cmd_calendar))
    u.dispatcher.add_handler(CommandHandler("markov", cmd_markov))
    u.dispatcher.add_handler(CommandHandler("roll", cmd_roll))
    u.dispatcher.add_handler(CommandHandler("r", cmd_roll))
    u.dispatcher.add_handler(CommandHandler("mm", cmd_mm))
    u.dispatcher.add_handler(CommandHandler("matchmaking", cmd_mm))
    u.dispatcher.add_handler(CommandHandler("cerca", cmd_cerca))
    u.dispatcher.add_handler(CommandHandler("search", cmd_cerca))
    u.dispatcher.add_handler(CommandHandler("diariosearch", cmd_cerca))
    u.dispatcher.add_handler(CallbackQueryHandler(on_callback_query))
    logger.info("Handlers registered.")
    u.start_polling()
    logger.info("Polling started.")
    u.idle()


if __name__ == "__main__":
    process(None)
