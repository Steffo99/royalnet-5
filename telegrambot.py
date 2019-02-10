import datetime
import random
import typing
import db
import errors
import stagismo
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
import cast
import re
import logging
import configparser
import markovify
import raven
import coloredlogs
import strings
import time
IKMarkup = telegram.InlineKeyboardMarkup
IKButton = telegram.InlineKeyboardButton

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
main_group_id = int(config["Telegram"]["main_group"])

discord_connection = None

# Init the Sentry client
sentry = raven.Client(config["Sentry"]["token"],
                      release=raven.fetch_git_sha(os.path.dirname(__file__)),
                      install_logging_hook=False,
                      hook_libraries=[])


def reply_msg(bot: telegram.Bot, chat_id: int, string: str, ignore_escaping=False, **kwargs) -> telegram.Message:
    string = strings.safely_format_string(string, ignore_escaping=ignore_escaping, words=kwargs)
    return bot.send_message(chat_id, string,
                            parse_mode="HTML",
                            disable_web_page_preview=True)


def reply(bot: telegram.Bot, update: telegram.Update, string: str, ignore_escaping=False, **kwargs) -> telegram.Message:
    while True:
        try:
            return reply_msg(bot, update.message.chat.id, string, ignore_escaping=ignore_escaping, **kwargs)
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
            # noinspection PyUnreachableCode
            if __debug__:
                raise
            logger.error(f"Critical error: {sys.exc_info()}")
            # noinspection PyBroadException
            try:
                reply_msg(bot, main_group_id, strings.TELEGRAM.ERRORS.CRITICAL_ERROR,
                          exc_info=sys.exc_info())
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
            # noinspection PyUnreachableCode
            if __debug__:
                raise
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
        reply(bot, update, strings.TELEGRAM.ERRORS.INACTIVE_BRIDGE)
        return
    # dirty hack as usual
    if update.message.text.endswith("full"):
        discord_connection.send("get cv full")
    else:
        discord_connection.send("get cv")
    message = discord_connection.recv()
    bot.send_message(update.message.chat.id, message, disable_web_page_preview=True, parse_mode="HTML")


@command
@database_access
def cmd_cast(bot: telegram.Bot, update: telegram.Update, session: db.Session):
    try:
        spell: str = update.message.text.split(" ", 1)[1]
    except IndexError:
        bot.send_message(update.message.chat.id, "⚠️ Non hai specificato nessun incantesimo!\n"
                                                 "Sintassi corretta: `/cast <nome_incantesimo>`", parse_mode="Markdown")
        return
    # Find a target for the spell
    target = random.sample(session.query(db.Telegram).all(), 1)[0]
    # END
    bot.send_message(update.message.chat.id, cast.cast(spell_name=spell,
                                                       target_name=target.username if target.username is not None
                                                       else target.first_name, platform="telegram"),
                     parse_mode="HTML")


@command
def cmd_color(bot: telegram.Bot, update: telegram.Update):
    reply(bot, update, strings.COLOR)


@command
def cmd_smecds(bot: telegram.Bot, update: telegram.Update):
    ds = random.sample(stagismo.listona, 1)[0]
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
        author = None
    except IndexError:
        if update.message.reply_to_message is None:
            reply(bot, update, strings.DIARIO.ERRORS.INVALID_SYNTAX)
            return
        text = update.message.reply_to_message.text
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
                       text=text)
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
                if match.creator != user:
                    bot.answer_callback_query(update.callback_query.id,
                                              show_alert=True,
                                              text=strings.MATCHMAKING.ERRORS.NOT_ADMIN)
                    return
                match.closed = True
                for player in match.players:
                    if player.status >= 1:
                        reply_msg(bot, player.user.telegram_id, strings.MATCHMAKING.GAME_START[player.status], **match.format_dict())
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
                inline_keyboard = IKMarkup([([IKButton(strings.MATCHMAKING.BUTTONS[key], callback_data=key)]) for key in strings.MATCHMAKING.BUTTONS])
            else:
                inline_keyboard = None
            try:
                bot.edit_message_text(message_id=update.callback_query.message.message_id,
                                      chat_id=config["Telegram"]["announcement_group"],
                                      text=match.generate_text(session),
                                      reply_markup=inline_keyboard,
                                      parse_mode="HTML")
            except BadRequest:
                pass
    except Exception:
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
    if "tonnuooooooro" in food.lower():
        reply(bot, update, strings.EAT.OUIJA, food=food)
        return
    reply(bot, update, strings.EAT.NORMAL, food=food)


@command
def cmd_ship(bot: telegram.Bot, update: telegram.Update):
    try:
        _, name_one, name_two = update.message.text.split(" ", 2)
    except ValueError:
        reply(bot, update, strings.SHIP.ERRORS.INVALID_SYNTAX)
        return
    name_one = name_one.lower()
    name_two = name_two.lower()
    part_one = re.search(r"^[A-Za-z][^aeiouAEIOU]*[aeiouAEIOU]?", name_one)
    part_two = re.search(r"[^aeiouAEIOU]*[aeiouAEIOU]?[A-Za-z]$", name_two)
    mixed = part_one.group(0) + part_two.group(0)  # TODO: find out what exceptions this could possibly raise
    if part_one is None or part_two is None:
        reply(bot, update, strings.SHIP.ERRORS.INVALID_NAMES)
        return
    reply(bot, update, strings.SHIP.RESULT,
          one=name_one.capitalize(),
          two=name_two.capitalize(),
          result=mixed.capitalize())


@command
def cmd_bridge(bot: telegram.Bot, update: telegram.Update):
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


@command
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
    if model is None:
        reply(bot, update, strings.MARKOV.ERRORS.NO_MODEL)
        return
    try:
        first_word = update.message.text.split(" ")[1]
    except IndexError:
        # Any word
        sentence = model.make_sentence(tries=1000)
        if sentence is None:
            reply(bot, update, strings.MARKOV.ERRORS.GENERATION_FAILED)
            return
        reply(bot, update, sentence)
        return
    # Specific word
    try:
        sentence = model.make_sentence_with_start(first_word, tries=1000)
    except KeyError:
        reply(bot, update, strings.MARKOV.ERRORS.MISSING_WORD)
        return
    if sentence is None:
        reply(bot, update, strings.MARKOV.ERRORS.SPECIFIC_WORD_FAILED)
        return
    reply(bot, update, sentence)


@command
def cmd_roll(bot: telegram.Bot, update: telegram.Update):
    dice_string = update.message.text.split(" ", 1)[1]
    try:
        result = dice.roll(f"{dice_string}t")
    except dice.DiceBaseException:
        reply(bot, update, strings.ROLL.ERRORS.INVALID_SYNTAX)
        return
    reply(bot, update, strings.ROLL.SUCCESS, result=result)


@command
def cmd_start(bot: telegram.Bot, update: telegram.Update):
    reply(bot, update, strings.TELEGRAM.BOT_STARTED)


def process(arg_discord_connection):
    if arg_discord_connection is not None:
        global discord_connection
        discord_connection = arg_discord_connection
    logger.info("Creating updater...")
    u = Updater(config["Telegram"]["bot_token"])
    logger.info("Registering handlers...")
    u.dispatcher.add_handler(CommandHandler("ping", cmd_ping))
    u.dispatcher.add_handler(CommandHandler("link", cmd_link))
    u.dispatcher.add_handler(CommandHandler("discord", cmd_cv))
    u.dispatcher.add_handler(CommandHandler("cv", cmd_cv))
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
    u.dispatcher.add_handler(CommandHandler("bridge", cmd_bridge))
    u.dispatcher.add_handler(CommandHandler("newevent", cmd_newevent))
    u.dispatcher.add_handler(CommandHandler("calendar", cmd_calendar))
    u.dispatcher.add_handler(CommandHandler("markov", cmd_markov))
    u.dispatcher.add_handler(CommandHandler("roll", cmd_roll))
    u.dispatcher.add_handler(CommandHandler("r", cmd_roll))
    u.dispatcher.add_handler(CommandHandler("mm", cmd_mm))
    u.dispatcher.add_handler(CommandHandler("matchmaking", cmd_mm))
    u.dispatcher.add_handler(CommandHandler("search", cmd_search))
    u.dispatcher.add_handler(CommandHandler("regex", cmd_regex))
    u.dispatcher.add_handler(CommandHandler("start", cmd_start))
    u.dispatcher.add_handler(CallbackQueryHandler(on_callback_query))
    logger.info("Handlers registered.")
    u.start_polling()
    logger.info("Polling started.")
    u.idle()


if __name__ == "__main__":
    process(None)
