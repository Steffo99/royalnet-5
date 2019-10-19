import datetime
import dateparser
import telegram
import asyncio
import re
import logging
import typing
from royalnet.commands import *
from royalnet.utils import asyncify, telegram_escape, sleep_until
from ..tables import MMEvent, MMDecision, MMResponse

log = logging.getLogger(__name__)


class MmCommand(Command):
    """Matchmaking command.

    Requires the MM_CHANNEL_ID envvar to be set."""
    name: str = "mm"

    aliases = ["matchmaking", "matchmake", "lfg", "lookingforgroup"]

    description: str = "Trova giocatori per una partita a qualcosa."

    syntax: str = "[ (data) ] (nomegioco)\n[descrizione]"

    tables = {MMEvent, MMDecision, MMResponse}

    _cycle_duration = 10

    @staticmethod
    def _main_keyboard(mmevent: MMEvent) -> typing.Optional[telegram.InlineKeyboardMarkup]:
        if mmevent.state == "WAITING":
            return telegram.InlineKeyboardMarkup([
                [telegram.InlineKeyboardButton("🔵 Ci sarò!", callback_data=f"mm_{mmevent.mmid}_d_YES")],
                [telegram.InlineKeyboardButton("⚫️ Forse...", callback_data=f"mm_{mmevent.mmid}_d_MAYBE")],
                [telegram.InlineKeyboardButton("🔴 Non mi interessa.", callback_data=f"mm_{mmevent.mmid}_d_NO")]
            ])
        elif mmevent.state == "DECISION":
            return telegram.InlineKeyboardMarkup([
                [telegram.InlineKeyboardButton("🔵 Ci sarò!", callback_data=f"mm_{mmevent.mmid}_d_YES"),
                 telegram.InlineKeyboardButton("🔴 Non mi interessa...", callback_data=f"mm_{mmevent.mmid}_d_NO")]
            ])
        elif mmevent.state == "READY_CHECK":
            return telegram.InlineKeyboardMarkup([
                [telegram.InlineKeyboardButton("🚩 Avvia la partita", callback_data=f"mm_{mmevent.mmid}_start")]
            ])
        elif mmevent.state == "STARTED":
            return None
        else:
            raise ValueError(f"state is of an unknown value ({mmevent.state})")

    @staticmethod
    def _main_text(mmevent: MMEvent):
        text = f"🌐 [{mmevent.datetime.strftime('%Y-%m-%d %H:%M')}] [b]{mmevent.title}[/b]\n"
        if mmevent.description:
            text += f"{mmevent.description}\n"
        text += "\n"
        if mmevent.state == "WAITING" or mmevent.state == "DECISION":
            for mmdecision in sorted(mmevent.decisions, key=lambda mmd: mmd.royal.username):
                mmdecision: "MMDecision"
                if mmdecision.decision == "YES":
                    text += "🔵 "
                elif mmdecision.decision == "MAYBE":
                    text += "⚫️ "
                elif mmdecision.decision == "NO":
                    text += "🔴 "
                else:
                    raise ValueError(f"decision is of an unknown value ({mmdecision.decision})")
                text += f"{mmdecision.royal}\n"
        elif mmevent.state == "READY_CHECK":
            for mmresponse in sorted(mmevent.responses, key=lambda mmr: mmr.royal.username):
                mmresponse: "MMResponse"
                if mmresponse.response is None:
                    text += "❔ "
                elif mmresponse.response == "YES":
                    text += "✅ "
                elif mmresponse.response == "LATER":
                    text += "🕒 "
                elif mmresponse.response == "NO":
                    text += "❌ "
                else:
                    raise ValueError(f"response is of an unknown value ({mmresponse.response})")
                text += f"{mmresponse.royal}\n"
        elif mmevent.state == "STARTED":
            for mmresponse in sorted(mmevent.responses, key=lambda mmr: mmr.response, reverse=True):
                if mmresponse.response == "YES":
                    text += f"✅ {mmresponse.royal}\n"
                elif mmresponse.response == "NO":
                    text += f"❌ {mmresponse.royal}\n"
        return text

    async def _run_mm(self, mmevent: MMEvent, session) -> None:
        client: telegram.Bot = self.interface.bot.client

        async def update_message() -> None:
            try:
                await self.interface.bot.safe_api_call(client.edit_message_text,
                                                       text=telegram_escape(self._main_text(mmevent)),
                                                       chat_id=-1001224004974,
                                                       message_id=mmevent.message_id,
                                                       parse_mode="HTML",
                                                       disable_web_page_preview=True,
                                                       reply_markup=self._main_keyboard(mmevent))
            except telegram.error.BadRequest:
                pass

        decision_string = f"⚫️ Hai detto che forse parteciperai a [b]{mmevent.title}[/b]" \
            f" alle [b]{mmevent.datetime.strftime('%H:%M')}[/b].\n" \
            f"Confermi di volerci essere? (Metti sì anche se arrivi un po' in ritardo!)"

        decision_keyboard = telegram.InlineKeyboardMarkup([
            [telegram.InlineKeyboardButton("🔵 Ci sarò!", callback_data=f"mm_{mmevent.mmid}_d_YES"),
             telegram.InlineKeyboardButton("🔴 Non mi interessa più.", callback_data=f"mm_{mmevent.mmid}_d_NO")]
        ])

        async def decision_yes(data: CommandData):
            royal = await data.get_author()
            mmdecision: MMDecision = await asyncify(
                session.query(self.interface.alchemy.MMDecision).filter_by(mmevent=mmevent,
                                                                                royal=royal).one_or_none)
            if mmdecision is None:
                mmdecision: MMDecision = self.interface.alchemy.MMDecision(royal=royal,
                                                                           mmevent=mmevent,
                                                                           decision="YES")
                session.add(mmdecision)
            else:
                mmdecision.decision = "YES"
            await asyncify(session.commit)
            await update_message()
            return "🔵 Hai detto che ci sarai!"

        async def decision_maybe(data: CommandData):
            royal = await data.get_author()
            mmdecision: MMDecision = await asyncify(
                session.query(self.interface.alchemy.MMDecision).filter_by(mmevent=mmevent,
                                                                                royal=royal).one_or_none)
            if mmdecision is None:
                mmdecision: MMDecision = self.interface.alchemy.MMDecision(royal=royal,
                                                                           mmevent=mmevent,
                                                                           decision="MAYBE")
                session.add(mmdecision)
            else:
                mmdecision.decision = "MAYBE"
            # Can't asyncify this
            session.commit()
            await update_message()
            return f"⚫️ Hai detto che forse ci sarai." \
                   f"Rispondi al messaggio di conferma {self._cycle_duration} minuti prima dell'inizio!"

        async def decision_no(data: CommandData):
            royal = await data.get_author()
            mmdecision: MMDecision = await asyncify(
                session.query(self.interface.alchemy.MMDecision).filter_by(mmevent=mmevent,
                                                                                royal=royal).one_or_none)
            if mmdecision is None:
                mmdecision: MMDecision = self.interface.alchemy.MMDecision(royal=royal,
                                                                           mmevent=mmevent,
                                                                           decision="NO")
                session.add(mmdecision)
            else:
                mmdecision.decision = "NO"
            # Can't asyncify this
            session.commit()
            await update_message()
            return "🔴 Hai detto che non ti interessa."

        def response_string() -> str:
            delay = (datetime.datetime.now() - mmevent.datetime).total_seconds()
            if delay < 60:
                return f"🚩 E' ora di [b]{mmevent.title}[/b]!\n" \
                    f"Sei pronto?"
            return f"🕒 Sei in ritardo di [b]{int(delay / 60)} minuti[/b] per [b]{mmevent.title}[/b]...\n" \
                f"Sei pronto?"

        response_keyboard = telegram.InlineKeyboardMarkup([
            [telegram.InlineKeyboardButton("✅ Ci sono!",
                                           callback_data=f"mm_{mmevent.mmid}_r_YES")],
            [telegram.InlineKeyboardButton("🕒 Aspettatemi ancora un po'!",
                                           callback_data=f"mm_{mmevent.mmid}_r_LATER")],
            [telegram.InlineKeyboardButton("❌ Non vengo più, mi spiace.",
                                           callback_data=f"mm_{mmevent.mmid}_r_NO")]
        ])

        async def response_yes(data: CommandData):
            royal = await data.get_author()
            mmresponse: MMResponse = await asyncify(
                session.query(self.interface.alchemy.MMResponse).filter_by(mmevent=mmevent,
                                                                                royal=royal).one_or_none)
            mmresponse.response = "YES"
            # Can't asyncify this
            session.commit()
            await update_message()
            return "✅ Sei pronto!"

        def later_string(royal) -> str:
            return f"🕒 {royal.username} ha chiesto di aspettare {self._cycle_duration} prima di iniziare la" \
                f" partita.\n\n" \
                f"Se vuoi iniziare la partita senza aspettarlo, premi Avvia partita su Royal Matchmaking!"

        async def response_later(data: CommandData):
            royal = await data.get_author()
            mmresponse: MMResponse = await asyncify(
                session.query(self.interface.alchemy.MMResponse).filter_by(mmevent=mmevent,
                                                                                royal=royal).one_or_none)
            mmresponse.response = "LATER"
            # Can't asyncify this
            session.commit()
            await self.interface.bot.safe_api_call(client.send_message,
                                                   chat_id=mmevent.creator.telegram[0].tg_id,
                                                   text=telegram_escape(later_string(royal)),
                                                   parse_mode="HTML",
                                                   disable_webpage_preview=True)
            await update_message()
            return f"🕒 Hai chiesto agli altri di aspettarti {self._cycle_duration} minuti."

        async def response_no(data: CommandData):
            royal = await data.get_author()
            mmresponse: MMResponse = await asyncify(
                session.query(self.interface.alchemy.MMResponse).filter_by(mmevent=mmevent,
                                                                                royal=royal).one_or_none)
            mmresponse.response = "NO"
            # Can't asyncify this
            session.commit()
            await update_message()
            return "❌ Hai detto che non ci sarai."

        def started_string():
            text = f"🚩 L'evento [b]{mmevent.title}[/b] è iniziato!\n\n" \
                f"Partecipano:\n"
            for mmresponse in sorted(mmevent.responses, key=lambda mmr: mmr.response, reverse=True):
                if mmresponse.response == "YES":
                    text += f"✅ {mmresponse.royal}\n"
                elif mmresponse.response == "NO":
                    text += f"❌ {mmresponse.royal}\n"
            return text

        started_without_you_string = f"🚩 Non hai confermato la tua presenza in tempo e [b]{mmevent.title}[/b] è" \
            f" iniziato senza di te.\n" \
            f"Mi dispiace!"

        async def start_event():
            mmevent.state = "STARTED"
            for mmresponse in mmevent.responses:
                if mmresponse.response is None:
                    mmresponse.response = "NO"
                if mmresponse.response == "LATER":
                    mmresponse.response = "NO"

                if mmresponse.response == "YES":
                    await self.interface.bot.safe_api_call(client.send_message,
                                                           chat_id=mmresponse.royal.telegram[0].tg_id,
                                                           text=telegram_escape(started_string()),
                                                           parse_mode="HTML",
                                                           disable_webpage_preview=True)
                else:
                    await self.interface.bot.safe_api_call(client.send_message,
                                                           chat_id=mmresponse.royal.telegram[0].tg_id,
                                                           text=telegram_escape(started_without_you_string),
                                                           parse_mode="HTML",
                                                           disable_webpage_preview=True)
            await asyncify(session.commit)
            await update_message()

        async def start_key(data: CommandData):
            royal = await data.get_author()
            if royal == mmevent.creator:
                await start_event()

        if mmevent.state == "WAITING":
            self.interface.register_keyboard_key(f"mm_{mmevent.mmid}_d_YES", decision_yes)
            self.interface.register_keyboard_key(f"mm_{mmevent.mmid}_d_MAYBE", decision_maybe)
            self.interface.register_keyboard_key(f"mm_{mmevent.mmid}_d_NO", decision_no)
            await sleep_until(mmevent.datetime - datetime.timedelta(minutes=10))
            self.interface.unregister_keyboard_key(f"mm_{mmevent.mmid}_d_YES")
            self.interface.unregister_keyboard_key(f"mm_{mmevent.mmid}_d_MAYBE")
            self.interface.unregister_keyboard_key(f"mm_{mmevent.mmid}_d_NO")
            mmevent.state = "DECISION"
            for mmdecision in mmevent.decisions:
                mmdecision: MMDecision
                if mmdecision.decision == "MAYBE":
                    await self.interface.bot.safe_api_call(client.send_message,
                                                           chat_id=mmdecision.royal.telegram[0].tg_id,
                                                           text=telegram_escape(decision_string),
                                                           parse_mode="HTML",
                                                           disable_webpage_preview=True,
                                                           reply_markup=decision_keyboard)
            await asyncify(session.commit)
            await update_message()

        if mmevent.state == "DECISION":
            self.interface.register_keyboard_key(f"mm_{mmevent.mmid}_d_YES", decision_yes)
            self.interface.register_keyboard_key(f"mm_{mmevent.mmid}_d_NO", decision_no)
            await sleep_until(mmevent.datetime)
            self.interface.unregister_keyboard_key(f"mm_{mmevent.mmid}_d_YES")
            self.interface.unregister_keyboard_key(f"mm_{mmevent.mmid}_d_NO")
            mmevent.state = "READY_CHECK"
            for mmdecision in mmevent.decisions:
                if mmdecision.decision == "MAYBE":
                    mmdecision.decision = "NO"
                elif mmdecision.decision == "YES":
                    mmresponse: MMResponse = self.interface.alchemy.MMResponse(royal=mmdecision.royal, mmevent=mmevent)
                    session.add(mmresponse)
            await asyncify(session.commit)
            await update_message()

        if mmevent.state == "READY_CHECK":
            self.interface.register_keyboard_key(f"mm_{mmevent.mmid}_r_YES", response_yes)
            self.interface.register_keyboard_key(f"mm_{mmevent.mmid}_r_LATER", response_later)
            self.interface.register_keyboard_key(f"mm_{mmevent.mmid}_r_NO", response_no)
            self.interface.register_keyboard_key(f"mm_{mmevent.mmid}_forcestart", start_key)
            cycle = 0
            while True:
                for mmresponse in mmevent.responses:
                    # Send messages
                    if mmresponse.response is None:
                        await self.interface.bot.safe_api_call(client.send_message,
                                                               chat_id=mmresponse.royal.telegram[0].tg_id,
                                                               text=telegram_escape(response_string()),
                                                               parse_mode="HTML",
                                                               disable_webpage_preview=True,
                                                               reply_markup=response_keyboard)
                # Wait
                await asyncio.sleep(60 * self._cycle_duration)
                # Advance cycle
                for mmresponse in mmevent.responses:
                    if mmresponse.response is None:
                        mmresponse.response = "NO"
                    if mmresponse.response == "LATER":
                        mmresponse.response = None
                # Check if the event can start
                for mmresponse in mmevent.responses:
                    if mmresponse.response is None:
                        break
                else:
                    break
                cycle += 1

            await start_event()
            self.interface.unregister_keyboard_key(f"mm_{mmevent.mmid}_r_YES")
            self.interface.unregister_keyboard_key(f"mm_{mmevent.mmid}_r_LATER")
            self.interface.unregister_keyboard_key(f"mm_{mmevent.mmid}_r_NO")
            self.interface.unregister_keyboard_key(f"mm_{mmevent.mmid}_forcestart")

    def __init__(self, interface):
        super().__init__(interface)
        # if self.interface.name != "telegram":
        #     return
        # log.debug("Loading pending MMEvents from the database")
        # session = interface.alchemy.Session()
        # mmevents = session.query(self.interface.alchemy.MMEvent) \
        #     .filter(self.interface.alchemy.MMEvent.datetime > datetime.datetime.now()) \
        #     .all()
        # log.info(f"Found {len(mmevents)} pending MMEvents")
        # for mmevent in mmevents:
        #     session = interface.alchemy.Session()
        #     new_mmevent = session.query(MMEvent).get(mmevent.mmid)
        #     interface.loop.create_task(self._run_mm(new_mmevent, session, close_at_end=True))
        # session.close()

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        raise UnsupportedError("MmCommand è attualmente disabilitato per via di bug introdotti da cambiamenti nella"
                               " gestione del database del bot.")
        # if self.interface.name != "telegram":
        #     raise UnsupportedError("mm is supported only on Telegram")
        # client: telegram.Bot = self.interface.bot.client
        # creator = await data.get_author(error_if_none=True)
        # try:
        #     timestring, title, description = args.match(r"\[\s*([^]]+)\s*]\s*([^\n]+)\s*\n?\s*(.+)?\s*", re.DOTALL)
        # except InvalidInputError:
        #     timestring, title, description = args.match(r"\s*(.+?)\s*\n\s*([^\n]+)\s*\n?\s*(.+)?\s*", re.DOTALL)
        # try:
        #     dt: typing.Optional[datetime.datetime] = dateparser.parse(timestring, settings={
        #         "PREFER_DATES_FROM": "future"
        #     })
        # except OverflowError:
        #     dt = None
        # if dt is None:
        #     await data.reply("⚠️ La data che hai specificato non è valida.")
        #     return
        # if dt <= datetime.datetime.now():
        #     await data.reply("⚠️ La data che hai specificato è nel passato.")
        #     return
        # mmevent: MMEvent = self.interface.alchemy.MMEvent(creator=creator,
        #                                                   datetime=dt,
        #                                                   title=title,
        #                                                   description=description,
        #                                                   state="WAITING")
        # data.session.add(mmevent)
        # await asyncify(data.session.commit)
        #
        # message: telegram.Message = await self.interface.bot.safe_api_call(client.send_message,
        #                                                                    chat_id=-1001287169422,
        #                                                                    text=telegram_escape(
        #                                                                        self._main_text(mmevent)),
        #                                                                    parse_mode="HTML",
        #                                                                    disable_webpage_preview=True,
        #                                                                    reply_markup=self._main_keyboard(mmevent))
        #
        # mmevent.message_id = message.message_id
        # # Can't asyncify this
        # await asyncify(data.session.commit)
        #
        # await self._run_mm(mmevent, data.session)
