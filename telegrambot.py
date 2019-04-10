import datetime
import random
import typing
import db
from utils import smecds, cast, errors, emojify, reply_msg
# python-telegram-bot has a different name
# noinspection PyPackageRequirements
import telegram
# noinspection PyPackageRequirements
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
# noinspection PyPackageRequirements
from telegram.error import TimedOut, Unauthorized, BadRequest, TelegramError
import dice
import sys
import os
import re
import logging
import configparser
import markovify
import raven
import coloredlogs
import strings
import time
import requests
IKMarkup = telegram.InlineKeyboardMarkup
IKButton = telegram.InlineKeyboardButton

# Markov models
try:
    with open("markovmodels/default.json") as file:
        default_model = markovify.Text.from_json(file.read())
except Exception:
    default_model = None
try:
    with open("markovmodels/dnd4.json") as file:
        dnd4_model = markovify.Text.from_json(file.read())
except Exception:
    dnd4_model = None

logging.getLogger().disabled = True
logger = logging.getLogger(__name__)
os.environ["COLOREDLOGS_LOG_FORMAT"] = "%(asctime)s %(levelname)s %(name)s %(message)s"
coloredlogs.install(level="DEBUG", logger=logger)

# Init the config reader
config = configparser.ConfigParser()
config.read("config.ini")
main_group_id = int(config["Telegram"]["main_group"])

discord_connection = None

# Init the Sentry client
sentry = raven.Client(config["Sentry"]["token"],
                      release=raven.fetch_git_sha(os.path.dirname(__file__)),
                      install_logging_hook=False,
                      hook_libraries=[])


def reply(bot: telegram.Bot, update: telegram.Update, string: str, ignore_escaping=False, disable_web_page_preview=True, **kwargs) -> telegram.Message:
    while True:
        try:
            return reply_msg(bot, update.message.chat.id, string, ignore_escaping=ignore_escaping, disable_web_page_preview=disable_web_page_preview, **kwargs)
        except Unauthorized:
            if update.message.chat.type == telegram.Chat.PRIVATE:
                return reply_msg(bot, main_group_id, strings.TELEGRAM.ERRORS.UNAUTHORIZED_USER,
                                 mention=update.message.from_user.mention_html())
            else:
                return reply_msg(bot, main_group_id, strings.TELEGRAM.ERRORS.UNAUTHORIZED_GROUP,
                                 group=(update.message.chat.title or update.message.chat.id))
        except TimedOut:
            time.sleep(1)
            pass


# noinspection PyUnresolvedReferences
def command(func: "function"):
    def new_func(bot: telegram.Bot, update: telegram.Update):
        # noinspection PyBroadException
        try:
            bot.send_chat_action(update.message.chat.id, telegram.ChatAction.TYPING)
            return func(bot, update)
        except TimedOut:
            logger.warning(f"Telegram timed out in {update}")
        except Exception:
            logger.error(f"Critical error: {sys.exc_info()}")
            # noinspection PyBroadException
            try:
                reply_msg(bot, main_group_id, strings.TELEGRAM.ERRORS.CRITICAL_ERROR,
                          exc_info=repr(sys.exc_info()))
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


# noinspection PyUnresolvedReferences
def database_access(func: "function"):
    def new_func(bot: telegram.Bot, update: telegram.Update):
        try:
            session = db.Session()
            return func(bot, update, session)
        except Exception:
            logger.error(f"Database error: {sys.exc_info()}")
            sentry.captureException()
        finally:
            try:
                session.close()
            except Exception:
                pass
    return new_func


@command
def cmd_ping(bot: telegram.Bot, update: telegram.Update):
    reply(bot, update, strings.PONG)


@command
@database_access
def cmd_link(bot: telegram.Bot, update: telegram.Update, session: db.Session):
    try:
        username = update.message.text.split(" ", 1)[1]
    except IndexError:
        reply(bot, update, strings.LINK.ERRORS.INVALID_SYNTAX)
        session.close()
        return
    try:
        t = db.Telegram.create(session,
                               royal_username=username,
                               telegram_user=update.message.from_user)
    except errors.NotFoundError:
        reply(bot, update, strings.LINK.ERRORS.NOT_FOUND)
        session.close()
        return
    except errors.AlreadyExistingError:
        reply(bot, update, strings.LINK.ERRORS.ALREADY_EXISTING)
        session.close()
        return
    session.add(t)
    session.commit()
    reply(bot, update, strings.LINK.SUCCESS)


@command
def cmd_cv(bot: telegram.Bot, update: telegram.Update):
    if discord_connection is None:
        reply(bot, update, strings.BRIDGE.ERRORS.INACTIVE_BRIDGE)
        return
    # dirty hack as usual
    if update.message.text.endswith("full"):
        discord_connection.send("get cv full")
    else:
        discord_connection.send("get cv")
    message = discord_connection.recv()
    reply(bot, update, message)


@command
def cmd_cast(bot: telegram.Bot, update: telegram.Update):
    reply(bot, update, strings.CAST.ERRORS.NOT_YET_AVAILABLE)


@command
def cmd_color(bot: telegram.Bot, update: telegram.Update):
    reply(bot, update, strings.COLOR)


@command
def cmd_smecds(bot: telegram.Bot, update: telegram.Update):
    ds = random.sample(smecds, 1)[0]
    reply(bot, update, strings.SMECDS, ds=ds)


@command
def cmd_ciaoruozi(bot: telegram.Bot, update: telegram.Update):
    if update.message.from_user.username.lstrip("@") == "MeStakes":
        reply(bot, update, strings.CIAORUOZI.THE_LEGEND_HIMSELF)
    else:
        reply(bot, update, strings.CIAORUOZI.SOMEBODY_ELSE)


@command
def cmd_ahnonlosoio(bot: telegram.Bot, update: telegram.Update):
    if update.message.reply_to_message is not None and update.message.reply_to_message.text in [
        "/ahnonlosoio", "/ahnonlosoio@royalgamesbot", strings.AHNONLOSOIO.ONCE, strings.AHNONLOSOIO.AGAIN
    ]:
        reply(bot, update, strings.AHNONLOSOIO.AGAIN)
    else:
        reply(bot, update, strings.AHNONLOSOIO.ONCE)


@command
@database_access
def cmd_balurage(bot: telegram.Bot, update: telegram.Update, session: db.Session):
    user = session.query(db.Telegram).filter_by(telegram_id=update.message.from_user.id).one_or_none()
    if user is None:
        reply(bot, update, strings.LINK.ERRORS.ROYALNET_NOT_LINKED)
        return
    try:
        reason = update.message.text.split(" ", 1)[1]
    except IndexError:
        reason = None
    br = db.BaluRage(royal_id=user.royal_id, reason=reason)
    session.add(br)
    session.commit()
    bot.send_message(update.message.chat.id, f"😡 Stai sfogando la tua ira sul bot!")


def parse_diario(session: db.Session, text: str):
    match = re.match(r'"?([^"]+)"? (?:—|-{1,2}) ?@?([A-Za-z0-9_]+)$', text)
    if match is None:
        return None, text
    text_string = match.group(1)
    author_string = match.group(2).lower()
    royal = session.query(db.Royal).filter(db.func.lower(db.Royal.username) == author_string).first()
    if royal is not None:
        author = royal.telegram[0]
        return author, text_string
    author = session.query(db.Telegram).filter(db.func.lower(db.Telegram.username) == author_string).first()
    if author is not None:
        return author, text_string
    return None, text_string


@command
@database_access
def cmd_diario(bot: telegram.Bot, update: telegram.Update, session: db.Session):
    user = session.query(db.Telegram).filter_by(telegram_id=update.message.from_user.id).one_or_none()
    if user is None:
        reply(bot, update, strings.LINK.ERRORS.ROYALNET_NOT_LINKED)
        return
    try:
        text = update.message.text.split(" ", 1)[1]
        saver = session.query(db.Telegram).filter_by(telegram_id=update.message.from_user.id).one_or_none()
        author, actual_text = parse_diario(session, text)
    except IndexError:
        if update.message.reply_to_message is None:
            reply(bot, update, strings.DIARIO.ERRORS.INVALID_SYNTAX)
            return
        text = update.message.reply_to_message.text
        if update.message.forward_from:
            author = session.query(db.Telegram) \
                .filter_by(telegram_id=update.message.forward_from.id) \
                .one_or_none()
        else:
            author = session.query(db.Telegram)\
                            .filter_by(telegram_id=update.message.reply_to_message.from_user.id)\
                            .one_or_none()
        saver = session.query(db.Telegram).filter_by(telegram_id=update.message.from_user.id).one_or_none()
    if text is None:
        reply(bot, update, strings.DIARIO.ERRORS.NO_TEXT)
        return
    diario = db.Diario(timestamp=datetime.datetime.now(),
                       saver=saver,
                       author=author,
                       text=actual_text)
    session.add(diario)
    session.commit()
    reply(bot, update, strings.DIARIO.SUCCESS, ignore_escaping=True, diario=diario.to_telegram())


@command
@database_access
def cmd_vote(bot: telegram.Bot, update: telegram.Update, session: db.Session):
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
    inline_keyboard = IKMarkup([[IKButton("🔵 Sì", callback_data="vote_yes")],
                                [IKButton("🔴 No", callback_data="vote_no")],
                                [IKButton("⚫️ Astieniti", callback_data="vote_abstain")]])
    message = bot.send_message(update.message.chat.id, vote.generate_text(session=session),
                               reply_markup=inline_keyboard,
                               parse_mode="HTML")
    vote.message_id = message.message_id
    session.commit()


def generate_search_message(term, entries):
    msg = strings.DIARIOSEARCH.HEADER.format(term=term)
    if len(entries) < 100:
        for entry in entries[:5]:
            msg += f'<a href="https://ryg.steffo.eu/diario#entry-{entry.id}">#{entry.id}</a> di <i>{entry.author or "Anonimo"}</i>\n{entry.text}\n\n'
        if len(entries) > 5:
            msg += "I termini comapiono anche nelle righe:\n"
            for entry in entries[5:]:
                msg += f'<a href="https://ryg.steffo.eu/diario#entry-{entry.id}">#{entry.id}</a> '
    else:
        for entry in entries[:100]:
            msg += f'<a href="https://ryg.steffo.eu/diario#entry-{entry.id}">#{entry.id}</a> '
        for entry in entries[100:]:
            msg += f"#{entry.id} "
    return msg


@command
@database_access
def cmd_search(bot: telegram.Bot, update: telegram.Update, session: db.Session):
    try:
        query = update.message.text.split(" ", 1)[1]
    except IndexError:
        reply(bot, update, strings.DIARIOSEARCH.ERRORS.INVALID_SYNTAX, command="search")
        return
    query = query.replace('%', '\\%').replace('_', '\\_')
    entries = session.query(db.Diario)\
                     .filter(db.Diario.text.op("~*")(r"(?:[\s\.,:;!?\"'<{([]+|^)"
                                                     + query +
                                                     r"(?:[\s\.,:;!?\"'>\})\]]+|$)"))\
                     .order_by(db.Diario.id.desc())\
                     .all()
    bot.send_message(update.message.chat.id, generate_search_message(f"<b>{query}</b>", entries), parse_mode="HTML")


@command
@database_access
def cmd_regex(bot: telegram.Bot, update: telegram.Update, session: db.Session):
    try:
        query = update.message.text.split(" ", 1)[1]
    except IndexError:
        reply(bot, update, strings.DIARIOSEARCH.ERRORS.INVALID_SYNTAX, command="regex")
        return
    query = query.replace('%', '\\%').replace('_', '\\_')
    entries = session.query(db.Diario).filter(db.Diario.text.op("~*")(query)).order_by(db.Diario.id.desc()).all()
    try:
        bot.send_message(update.message.chat.id, generate_search_message(f"<code>{query}</code>", entries), parse_mode="HTML")
    except (BadRequest, TelegramError):
        reply(bot, update, strings.DIARIOSEARCH.ERRORS.RESULTS_TOO_LONG)


@command
@database_access
def cmd_mm(bot: telegram.Bot, update: telegram.Update, session: db.Session):
    user = session.query(db.Telegram).filter_by(telegram_id=update.message.from_user.id).one_or_none()
    if user is None:
        reply(bot, update, strings.LINK.ERRORS.ROYALNET_NOT_LINKED)
        return
    match = re.match(r"/(?:mm|matchmaking)(?:@royalgamesbot)?(?: (?:([0-9]+)-)?([0-9]+))? (?:per )?([A-Za-z0-9!\-_. ]+)(?:.*\n(.+))?",
                     update.message.text)
    if match is None:
        reply(bot, update, strings.MATCHMAKING.ERRORS.INVALID_SYNTAX)
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
    inline_keyboard = IKMarkup([([IKButton(strings.MATCHMAKING.BUTTONS[key], callback_data=key)]) for key in strings.MATCHMAKING.BUTTONS])
    message = bot.send_message(config["Telegram"]["announcement_group"], db_match.generate_text(session=session),
                               parse_mode="HTML",
                               reply_markup=inline_keyboard)
    db_match.message_id = message.message_id
    session.commit()


def on_callback_query(bot: telegram.Bot, update: telegram.Update):
    try:
        session = db.Session()
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
            user = session.query(db.Telegram).filter_by(telegram_id=update.callback_query.from_user.id).one_or_none()
            if user is None:
                bot.answer_callback_query(update.callback_query.id, show_alert=True,
                                          text=strings.LINK.ERRORS.ROYALNET_NOT_LINKED,
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
            inline_keyboard = IKMarkup([[IKButton("🔵 Sì", callback_data="vote_yes")],
                                        [IKButton("🔴 No", callback_data="vote_no")],
                                        [IKButton("⚫️ Astieniti", callback_data="vote_abstain")]])
            bot.edit_message_text(message_id=update.callback_query.message.message_id,
                                  chat_id=update.callback_query.message.chat.id,
                                  text=question.generate_text(session),
                                  reply_markup=inline_keyboard,
                                  parse_mode="HTML")
        elif update.callback_query.data.startswith("match_"):
            user = session.query(db.Telegram).filter_by(telegram_id=update.callback_query.from_user.id).one_or_none()
            if user is None:
                bot.answer_callback_query(update.callback_query.id,
                                          show_alert=True,
                                          text=strings.LINK.ERRORS.ROYALNET_NOT_LINKED,
                                          parse_mode="Markdown")
                return
            match = session.query(db.Match).filter_by(message_id=update.callback_query.message.message_id).one()
            if update.callback_query.data == "match_close":
                if not (match.creator == user or user.telegram_id == 25167391):
                    bot.answer_callback_query(update.callback_query.id,
                                              show_alert=True,
                                              text=strings.MATCHMAKING.ERRORS.NOT_ADMIN)
                    return
                match.closed = True
                for partecipation in match.players:
                    if int(partecipation.status) >= 1:
                        try:
                            reply_msg(bot, partecipation.user.telegram_id, strings.MATCHMAKING.GAME_START[int(partecipation.status)], **match.format_dict())
                        except Unauthorized:
                            reply_msg(bot, main_group_id, strings.TELEGRAM.ERRORS.UNAUTHORIZED_USER,
                                      mention=partecipation.user.mention())
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
                partecipation = session.query(db.MatchPartecipation).filter_by(match=match, user=user).one_or_none()
                if partecipation is None:
                    partecipation = db.MatchPartecipation(match=match, status=status.value, user=user)
                    session.add(partecipation)
                else:
                    partecipation.status = status.value
            session.commit()
            bot.answer_callback_query(update.callback_query.id,
                                      text=strings.MATCHMAKING.TICKER_TEXT[update.callback_query.data],
                                      cache_time=1)
            if not match.closed:
                inline_keyboard = IKMarkup([([IKButton(strings.MATCHMAKING.BUTTONS[key], callback_data=key)]) for key in strings.MATCHMAKING.BUTTONS])
            else:
                inline_keyboard = None
            while True:
                try:
                    bot.edit_message_text(message_id=update.callback_query.message.message_id,
                                          chat_id=config["Telegram"]["announcement_group"],
                                          text=match.generate_text(session),
                                          reply_markup=inline_keyboard,
                                          parse_mode="HTML")
                    break
                except BadRequest:
                    break
                except TimedOut:
                    time.sleep(1)
    except Exception:
        try:
            bot.answer_callback_query(update.callback_query.id,
                                      show_alert=True,
                                      text=strings.TELEGRAM.ERRORS.CRITICAL_ERROR_QUERY)
        except Exception:
            pass
        logger.error(f"Critical error: {sys.exc_info()}")
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
    finally:
        try:
            # noinspection PyUnboundLocalVariable
            session.close()
        except Exception:
            pass


@command
def cmd_eat(bot: telegram.Bot, update: telegram.Update):
    try:
        food: str = update.message.text.split(" ", 1)[1].capitalize()
    except IndexError:
        reply(bot, update, strings.EAT.ERRORS.INVALID_SYNTAX)
        return
    reply(bot, update, strings.EAT.FOODS.get(food.lower(), strings.EAT.FOODS["_default"]), food=food)


@command
def cmd_ship(bot: telegram.Bot, update: telegram.Update):
    try:
        names = update.message.text.split(" ")
        name_one = names[1]
        name_two = names[2]
    except ValueError:
        reply(bot, update, strings.SHIP.ERRORS.INVALID_SYNTAX)
        return
    name_one = name_one.lower()
    name_two = name_two.lower()
    match_one = re.search(r"^[A-Za-z][^aeiouAEIOU]*[aeiouAEIOU]?", name_one)
    if match_one is None:
        part_one = name_one[:int(len(name_one) / 2)]
    else:
        part_one = match_one.group(0)
    match_two = re.search(r"[^aeiouAEIOU]*[aeiouAEIOU]?[A-Za-z]$", name_two)
    if match_two is None:
        part_two = name_two[int(len(name_two) / 2):]
    else:
        part_two = match_two.group(0)
    mixed = part_one + part_two  # TODO: find out what exceptions this could possibly raise
    reply(bot, update, strings.SHIP.RESULT,
          one=name_one.capitalize(),
          two=name_two.capitalize(),
          result=mixed.capitalize())


@command
def cmd_bridge(bot: telegram.Bot, update: telegram.Update):
    if discord_connection is None:
        reply(bot, update, strings.BRIDGE.ERRORS.INACTIVE_BRIDGE)
        return
    try:
        data = update.message.text.split(" ", 1)[1]
    except IndexError:
        reply(bot, update, strings.BRIDGE.ERRORS.INVALID_SYNTAX)
        return
    discord_connection.send(f"!{data}")
    result = discord_connection.recv()
    if result == "error":
        reply(bot, update, strings.BRIDGE.FAILURE)
    if result == "success":
        reply(bot, update, strings.BRIDGE.SUCCESS)


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


@command
@database_access
def cmd_newevent(bot: telegram.Bot, update: telegram.Update, session: db.Session):
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
    bot.send_message(update.message.chat.id, "✅ Evento aggiunto al Calendario Royal Games!")


@command
@database_access
def cmd_calendar(bot: telegram.Bot, update: telegram.Update, session: db.Session):
    next_events = session.query(db.Event).filter(db.Event.time > datetime.datetime.now()).order_by(db.Event.time).all()
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


@command
def cmd_markov(bot: telegram.Bot, update: telegram.Update):
    if default_model is None:
        reply(bot, update, strings.MARKOV.ERRORS.NO_MODEL)
        return
    try:
        first_word = update.message.text.split(" ")[1]
    except IndexError:
        # Any word
        sentence = default_model.make_sentence(tries=1000)
        if sentence is None:
            reply(bot, update, strings.MARKOV.ERRORS.GENERATION_FAILED)
            return
        reply(bot, update, sentence)
        return
    # Specific word
    try:
        sentence = default_model.make_sentence_with_start(first_word, tries=1000)
    except KeyError:
        reply(bot, update, strings.MARKOV.ERRORS.MISSING_WORD)
        return
    if sentence is None:
        reply(bot, update, strings.MARKOV.ERRORS.SPECIFIC_WORD_FAILED)
        return
    reply(bot, update, sentence)


@command
def cmd_dndmarkov(bot: telegram.Bot, update: telegram.Update):
    if dnd4_model is None:
        reply(bot, update, strings.MARKOV.ERRORS.NO_MODEL)
        return
    try:
        first_word = update.message.text.split(" ")[1]
    except IndexError:
        # Any word
        sentence = dnd4_model.make_sentence(tries=1000)
        if sentence is None:
            reply(bot, update, strings.MARKOV.ERRORS.GENERATION_FAILED)
            return
        reply(bot, update, sentence)
        return
    # Specific word
    try:
        sentence = dnd4_model.make_sentence_with_start(first_word, tries=1000)
    except KeyError:
        reply(bot, update, strings.MARKOV.ERRORS.MISSING_WORD)
        return
    if sentence is None:
        reply(bot, update, strings.MARKOV.ERRORS.SPECIFIC_WORD_FAILED)
        return
    reply(bot, update, sentence)


def exec_roll(roll) -> str:
    result = int(roll.evaluate())
    string = ""
    if isinstance(roll, dice.elements.Dice):
        string += f"<b>{result}</b>"
    else:
        for index, operand in enumerate(roll.original_operands):
            if operand != roll.operands[index]:
                string += f"<i>{roll.operands[index]}</i>"
            else:
                string += f"{operand}"
            if index + 1 != len(roll.original_operands):

                string += strings.ROLL.SYMBOLS[roll.__class__]
        string += f"=<b>{result}</b>"
    return string


@command
def cmd_roll(bot: telegram.Bot, update: telegram.Update):
    dice_string = update.message.text.split(" ", 1)[1]
    try:
        roll = dice.roll(f"{dice_string}", raw=True)
    except dice.DiceBaseException:
        reply(bot, update, strings.ROLL.ERRORS.INVALID_SYNTAX)
        return
    try:
        result = exec_roll(roll)
    except dice.DiceFatalException:
        reply(bot, update, strings.ROLL.ERRORS.DICE_ERROR)
        return
    reply(bot, update, strings.ROLL.SUCCESS, result=result, ignore_escaping=True)


@command
def cmd_start(bot: telegram.Bot, update: telegram.Update):
    reply(bot, update, strings.TELEGRAM.BOT_STARTED)


@command
def cmd_spell(bot: telegram.Bot, update: telegram.Update):
    try:
        spell_name: str = update.message.text.split(" ", 1)[1]
    except IndexError:
        reply(bot, update, strings.SPELL.ERRORS.INVALID_SYNTAX)
        return
    spell = cast.Spell(spell_name)
    reply(bot, update, spell.stringify())


@command
def cmd_emojify(bot: telegram.Bot, update: telegram.Update):
    try:
        string: str = update.message.text.split(" ", 1)[1]
    except IndexError:
        reply(bot, update, strings.EMOJIFY.ERRORS.INVALID_SYNTAX)
        return
    msg = emojify(string)
    reply(bot, update, strings.EMOJIFY.RESPONSE, emojified=msg)


@command
def cmd_pug(bot: telegram.Bot, update: telegram.Update):
    if update.effective_chat.type != telegram.Chat.PRIVATE:
        reply(bot, update, strings.PUG.ERRORS.PRIVATE_CHAT_ONLY)
        return
    j = requests.get("https://dog.ceo/api/breed/pug/images/random").json()
    reply(bot, update, strings.PUG.HERE_HAVE_A_PUG, disable_web_page_preview=False, image_url=j["message"])


def process(arg_discord_connection):
    if arg_discord_connection is not None:
        global discord_connection
        discord_connection = arg_discord_connection
    logger.info("Creating updater...")
    u = Updater(config["Telegram"]["bot_token"])
    logger.info("Registering handlers...")
    u.dispatcher.add_handler(CommandHandler("ping", cmd_ping))
    u.dispatcher.add_handler(CommandHandler("pong", cmd_ping))
    u.dispatcher.add_handler(CommandHandler("link", cmd_link))
    u.dispatcher.add_handler(CommandHandler("discord", cmd_cv))
    u.dispatcher.add_handler(CommandHandler("cv", cmd_cv))
    u.dispatcher.add_handler(CommandHandler("cast", cmd_cast))
    u.dispatcher.add_handler(CommandHandler("color", cmd_color))
    u.dispatcher.add_handler(CommandHandler("error", cmd_color))
    u.dispatcher.add_handler(CommandHandler("smecds", cmd_smecds))
    u.dispatcher.add_handler(CommandHandler("ciaoruozi", cmd_ciaoruozi))
    u.dispatcher.add_handler(CommandHandler("ahnonlosoio", cmd_ahnonlosoio))
    u.dispatcher.add_handler(CommandHandler("balurage", cmd_balurage))
    u.dispatcher.add_handler(CommandHandler("diario", cmd_diario))
    u.dispatcher.add_handler(CommandHandler("spaggia", cmd_diario))
    u.dispatcher.add_handler(CommandHandler("spaggio", cmd_diario))
    u.dispatcher.add_handler(CommandHandler("vote", cmd_vote))
    u.dispatcher.add_handler(CommandHandler("eat", cmd_eat))
    u.dispatcher.add_handler(CommandHandler("ship", cmd_ship))
    u.dispatcher.add_handler(CommandHandler("bridge", cmd_bridge))
    u.dispatcher.add_handler(CommandHandler("newevent", cmd_newevent))
    u.dispatcher.add_handler(CommandHandler("calendar", cmd_calendar))
    u.dispatcher.add_handler(CommandHandler("markov", cmd_markov))
    u.dispatcher.add_handler(CommandHandler("dndmarkov", cmd_dndmarkov))
    u.dispatcher.add_handler(CommandHandler("roll", cmd_roll))
    u.dispatcher.add_handler(CommandHandler("r", cmd_roll))
    u.dispatcher.add_handler(CommandHandler("mm", cmd_mm))
    u.dispatcher.add_handler(CommandHandler("matchmaking", cmd_mm))
    u.dispatcher.add_handler(CommandHandler("search", cmd_search))
    u.dispatcher.add_handler(CommandHandler("regex", cmd_regex))
    u.dispatcher.add_handler(CommandHandler("start", cmd_start))
    u.dispatcher.add_handler(CommandHandler("spell", cmd_spell))
    u.dispatcher.add_handler(CommandHandler("emojify", cmd_emojify))
    u.dispatcher.add_handler(CommandHandler("pug", cmd_pug))
    u.dispatcher.add_handler(CommandHandler("carlino", cmd_pug))
    u.dispatcher.add_handler(CommandHandler("carlini", cmd_pug))
    u.dispatcher.add_handler(CallbackQueryHandler(on_callback_query))
    logger.info("Handlers registered.")
    u.start_polling()
    logger.info("Polling started.")
    u.idle()


if __name__ == "__main__":
    process(None)
