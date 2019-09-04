import typing
import datetime
import dateparser
import os
import telegram
import asyncio
from ..command import Command
from ..commandargs import CommandArgs
from ..commanddata import CommandData
from ...database.tables import MMEvent, MMDecision, MMResponse
from ...error import *
from ...utils import asyncify, telegram_escape, sleep_until


class MmCommand(Command):
    """Matchmaking command.

    Requires the MM_CHANNEL_ID envvar to be set."""
    name: str = "mm"

    description: str = "Trova giocatori per una partita a qualcosa."

    syntax: str = "[ (data) ] (nomegioco)\n[descrizione]"

    require_alchemy_tables = {MMEvent, MMDecision, MMResponse}

    @staticmethod
    def _decision_string(mmevent: MMEvent) -> str:
        return f"⚫️ Hai detto che forse parteciperai a [b]{mmevent.title}[/b] alle [b]{mmevent.datetime.strftime('%H:%M')}[/b].\n" \
               f"Confermi di volerci essere?"

    @staticmethod
    def _decision_keyboard(mmevent: MMEvent) -> telegram.InlineKeyboardMarkup:
        return telegram.InlineKeyboardMarkup([
            [telegram.InlineKeyboardButton("🔵 Ci sarò!", callback_data=f"mm_{mmevent.mmid}_d_YES"),
             telegram.InlineKeyboardButton("🔴 Non mi interessa...", callback_data=f"mm_{mmevent.mmid}_d_NO")]
        ])

    @staticmethod
    def _response_string(mmevent: MMEvent, count: int = 0) -> str:
        if count == 0:
            return f"🚩 E' ora di [b]{mmevent.title}[/b]!\n" \
                   f"Sei pronto?"
        else:
            return f"🕒 Sei in ritardo di [b]{count * 5}[/b] minuti per [b]{mmevent.title}[/b]...\n" \
                   f"Sei pronto?"

    @staticmethod
    def _response_keyboard(mmevent: MMEvent) -> telegram.InlineKeyboardMarkup:
        return telegram.InlineKeyboardMarkup([
            [telegram.InlineKeyboardButton("✅ Ci sono!", callback_data=f"mm_{mmevent.mmid}_r_YES")],
            [telegram.InlineKeyboardButton("🕒 Aspettatemi 5 minuti!", callback_data=f"mm_{mmevent.mmid}_r_LATER")],
            [telegram.InlineKeyboardButton("❌ Non ci sono più, mi spiace.", callback_data=f"mm_{mmevent.mmid}_r_NO")]
        ])

    async def _update_message(self, mmevent: MMEvent) -> None:
        client: telegram.Bot = self.interface.bot.client
        try:
            await asyncify(client.edit_message_text,
                           text=telegram_escape(str(mmevent)),
                           chat_id=os.environ["MM_CHANNEL_ID"],
                           message_id=mmevent.message_id,
                           parse_mode="HTML",
                           disable_web_page_preview=True,
                           reply_markup=mmevent.main_keyboard())
        except telegram.error.BadRequest:
            pass

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        if self.interface.name != "telegram":
            raise UnsupportedError("mm is supported only on Telegram")
        client: telegram.Bot = self.interface.bot.client
        creator = await data.get_author(error_if_none=True)
        timestring, title, description = args.match(r"\[\s*([^]]+)\s*]\s*([^\n]+)\s*\n?\s*(.+)?\s*")

        try:
            dt: typing.Optional[datetime.datetime] = dateparser.parse(timestring)
        except OverflowError:
            dt = None
        if dt is None:
            await data.reply("⚠️ La data che hai specificato non è valida.")
            return
        if dt <= datetime.datetime.now():
            await data.reply("⚠️ La data che hai specificato è nel passato.")
            return

        mmevent: MMEvent = self.interface.alchemy.MMEvent(creator=creator,
                                                          datetime=dt,
                                                          title=title,
                                                          description=description,
                                                          state="WAITING")
        self.interface.session.add(mmevent)
        await asyncify(self.interface.session.commit)

        async def decision_yes(data: CommandData):
            royal = await data.get_author()
            mmdecision: MMDecision = await asyncify(self.interface.session.query(self.interface.alchemy.MMDecision).filter_by(mmevent=mmevent, royal=royal).one_or_none)
            if mmdecision is None:
                mmdecision: MMDecision = self.interface.alchemy.MMDecision(royal=royal,
                                                                           mmevent=mmevent,
                                                                           decision="YES")
                self.interface.session.add(mmdecision)
            else:
                mmdecision.decision = "YES"
            # Can't asyncify this
            self.interface.session.commit()
            await self._update_message(mmevent)
            return "🔵 Hai detto che ci sarai!"

        async def decision_maybe(data: CommandData):
            royal = await data.get_author()
            mmdecision: MMDecision = await asyncify(self.interface.session.query(self.interface.alchemy.MMDecision).filter_by(mmevent=mmevent, royal=royal).one_or_none)
            if mmdecision is None:
                mmdecision: MMDecision = self.interface.alchemy.MMDecision(royal=royal,
                                                                           mmevent=mmevent,
                                                                           decision="MAYBE")
                self.interface.session.add(mmdecision)
            else:
                mmdecision.decision = "MAYBE"
            # Can't asyncify this
            self.interface.session.commit()
            await self._update_message(mmevent)
            return "⚫️ Hai detto che forse ci sarai. Rispondi al messaggio di conferma 5 minuti prima dell'inizio!"

        async def decision_no(data: CommandData):
            royal = await data.get_author()
            mmdecision: MMDecision = await asyncify(self.interface.session.query(self.interface.alchemy.MMDecision).filter_by(mmevent=mmevent, royal=royal).one_or_none)
            if mmdecision is None:
                mmdecision: MMDecision = self.interface.alchemy.MMDecision(royal=royal,
                                                                           mmevent=mmevent,
                                                                           decision="NO")
                self.interface.session.add(mmdecision)
            else:
                mmdecision.decision = "NO"
            # Can't asyncify this
            self.interface.session.commit()
            await self._update_message(mmevent)
            return "🔴 Hai detto che non ti interessa."

        self.interface.register_keyboard_key(f"mm_{mmevent.mmid}_d_YES", decision_yes)
        self.interface.register_keyboard_key(f"mm_{mmevent.mmid}_d_MAYBE", decision_maybe)
        self.interface.register_keyboard_key(f"mm_{mmevent.mmid}_d_NO", decision_no)

        message: telegram.Message = await asyncify(client.send_message,
                                                   chat_id=os.environ["MM_CHANNEL_ID"],
                                                   text=telegram_escape(str(mmevent)),
                                                   parse_mode="HTML",
                                                   disable_webpage_preview=True,
                                                   reply_markup=mmevent.main_keyboard())

        mmevent.message_id = message.message_id
        # Can't asyncify this
        self.interface.session.commit()

        await sleep_until(dt - datetime.timedelta(minutes=10))

        mmevent.state = "DECISION"
        await asyncify(self.interface.session.commit)
        for mmdecision in mmevent.decisions:
            mmdecision: MMDecision
            if mmdecision.decision == "MAYBE":
                await asyncify(client.send_message,
                               chat_id=mmdecision.royal.telegram[0].tg_id,
                               text=telegram_escape(self._decision_string(mmevent)),
                               parse_mode="HTML",
                               disable_webpage_preview=True,
                               reply_markup=self._decision_keyboard(mmevent))
        await self._update_message(mmevent)

        await sleep_until(dt)

        async def response_yes(data: CommandData):
            royal = await data.get_author()
            mmresponse: MMResponse = await asyncify(
                self.interface.session.query(self.interface.alchemy.MMResponse).filter_by(mmevent=mmevent, royal=royal).one_or_none)
            mmresponse.response = "YES"
            # Can't asyncify this
            self.interface.session.commit()
            await self._update_message(mmevent)
            return "✅ Sei pronto!"

        async def response_later(data: CommandData):
            royal = await data.get_author()
            mmresponse: MMResponse = await asyncify(
                self.interface.session.query(self.interface.alchemy.MMResponse).filter_by(mmevent=mmevent, royal=royal).one_or_none)
            mmresponse.response = "LATER"
            # Can't asyncify this
            self.interface.session.commit()
            await self._update_message(mmevent)
            return "🕒 Hai chiesto agli altri di aspettarti 5 minuti."

        async def response_no(data: CommandData):
            royal = await data.get_author()
            mmresponse: MMResponse = await asyncify(
                self.interface.session.query(self.interface.alchemy.MMResponse).filter_by(mmevent=mmevent, royal=royal).one_or_none)
            mmresponse.response = "NO"
            # Can't asyncify this
            self.interface.session.commit()
            await self._update_message(mmevent)
            return "❌ Hai detto che non ci sarai."

        async def start_now():
            mmevent.state = "STARTED"
            for mmresponse in mmevent.responses:
                if mmresponse.response is None:
                    mmresponse.response = "NO"
                if mmresponse.response == "LATER":
                    mmresponse.response = "NO"
            await self._update_message(mmevent)
            await asyncify(self.interface.session.commit)
            self.interface.unregister_keyboard_key(f"mm_{mmevent.mmid}_r_YES")
            self.interface.unregister_keyboard_key(f"mm_{mmevent.mmid}_r_LATER")
            self.interface.unregister_keyboard_key(f"mm_{mmevent.mmid}_r_NO")
            self.interface.unregister_keyboard_key(f"mm_{mmevent.mmid}_start")

        async def start_key(data: CommandData):
            royal = await data.get_author()
            if royal == creator:
                await start_now()

        mmevent.state = "READY_CHECK"

        self.interface.unregister_keyboard_key(f"mm_{mmevent.mmid}_d_YES")
        self.interface.unregister_keyboard_key(f"mm_{mmevent.mmid}_d_MAYBE")
        self.interface.unregister_keyboard_key(f"mm_{mmevent.mmid}_d_NO")

        for mmdecision in mmevent.decisions:
            if mmdecision.decision == "MAYBE":
                mmdecision.decision = "NO"
            elif mmdecision.decision == "YES":
                mmresponse: MMResponse = self.interface.alchemy.MMResponse(royal=mmdecision.royal, mmevent=mmevent)
                self.interface.session.add(mmresponse)
        await asyncify(self.interface.session.commit)

        self.interface.register_keyboard_key(f"mm_{mmevent.mmid}_r_YES", response_yes)
        self.interface.register_keyboard_key(f"mm_{mmevent.mmid}_r_LATER", response_later)
        self.interface.register_keyboard_key(f"mm_{mmevent.mmid}_r_NO", response_no)
        self.interface.register_keyboard_key(f"mm_{mmevent.mmid}_start", start_key)

        count = 0
        while True:
            for mmresponse in mmevent.responses:
                # Send messages
                if mmresponse.response is None:
                    await asyncify(client.send_message,
                                   chat_id=mmresponse.royal.telegram[0].tg_id,
                                   text=telegram_escape(self._response_string(mmevent, count=count)),
                                   parse_mode="HTML",
                                   disable_webpage_preview=True,
                                   reply_markup=self._response_keyboard(mmevent))
            await self._update_message(mmevent)
            # Wait
            await asyncio.sleep(300)

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

            count += 1

        await start_now()
