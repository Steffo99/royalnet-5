import datetime
from telegram import Bot as PTBBot
from telegram import Message as PTBMessage
from telegram.error import BadRequest, Unauthorized
from telegram import InlineKeyboardMarkup as IKM
from telegram import InlineKeyboardButton as IKB
from royalnet.commands import *
from royalnet.bots import TelegramBot
from royalnet.utils import telegram_escape, asyncify, sleep_until
from ..tables import MMEvent, MMResponse, User, Telegram
from ..utils import MMChoice, MMInterfaceData, MMInterfaceDataTelegram


class MatchmakingCommand(Command):
    name: str = "matchmaking"

    description: str = "Cerca persone per una partita a qualcosa!"

    syntax: str = "[ {ora} ] {nome}\n[descrizione]"

    aliases = ["mm", "lfg"]

    tables = {MMEvent, MMResponse}

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        # Find all relevant MMEvents and run them
        session = self.interface.Session()
        mmevents = await asyncify(
            session.query(self.alchemy.MMEvent)
                   .filter(self.alchemy.MMEvent.interface == self.interface.name,
                           self.alchemy.MMEvent.datetime > datetime.datetime.now())
                   .all
        )
        for mmevent in mmevents:
            self._run_mmevent(mmevent.mmid)

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        # Create a new MMEvent and run it
        if self.interface.name != "telegram":
            raise UnsupportedError(f"{self.interface.prefix}matchmaking funziona solo su Telegram. Per ora.")
        author = await data.get_author(error_if_none=True)
        ...

    _mm_chat_id = -1001224004974

    _mm_error_chat_id = -1001153723135

    def _gen_mm_message(self, mmevent: MMEvent) -> str:
        text = f"🌐 [{mmevent.datetime.strftime('%Y-%m-%d %H:%M')}] [b]{mmevent.title}[/b]\n"
        if mmevent.description:
            text += f"{mmevent.description}\n"
        text += "\n"
        for response in mmevent.responses:
            response: MMResponse
            text += f"{response.choice.value} {response.user}\n"
        return text

    def _gen_telegram_keyboard(self, mmevent: MMEvent):
        return IKM([
            [IKB(f"{MMChoice.YES.value} Ci sarò!", callback_data=f"mm{mmevent.mmid}_YES")],
            [IKB(f"{MMChoice.MAYBE.value} (Forse.)", callback_data=f"mm{mmevent.mmid}_MAYBE")],
            [IKB(f"{MMChoice.LATE_SHORT.value} Arrivo dopo 5-10 min.", callback_data=f"mm{mmevent.mmid}_LATE_SHORT")],
            [IKB(f"{MMChoice.LATE_MEDIUM.value} Arrivo dopo 15-35 min.",
                 callback_data=f"mm{mmevent.mmid}_LATE_MEDIUM")],
            [IKB(f"{MMChoice.LATE_LONG.value} Arrivo dopo 40+ min.", callback_data=f"mm{mmevent.mmid}_LATE_LONG")],
            [IKB(f"{MMChoice.NO_TIME} Non posso a quell'ora...", callback_data=f"mm{mmevent.mmid}_NO_TIME")],
            [IKB(f"{MMChoice.NO_INTEREST} Non mi interessa.", callback_data=f"mm{mmevent.mmid}_NO_INTEREST")],
            [IKB(f"{MMChoice.NO_TECH} Ho un problema!", callback_data=f"mm{mmevent.mmid}_NO_TECH")],
        ])

    async def _update_telegram_mm_message(self, client: PTBBot, mmevent: MMEvent):
        try:
            await self.interface.bot.safe_api_call(client.edit_message_text,
                                                   chat_id=self._mm_chat_id,
                                                   text=telegram_escape(self._gen_mm_message(mmevent)),
                                                   message_id=mmevent.interface_data,
                                                   parse_mode="HTML",
                                                   disable_web_page_preview=True,
                                                   reply_markup=self._gen_telegram_keyboard(mmevent))
        except BadRequest:
            pass

    def _gen_mm_telegram_callback(self, client: PTBBot, mmid: int, choice: MMChoice):
        async def callback(data: CommandData):
            author = await data.get_author(error_if_none=True)
            # Find the MMEvent with the current session
            mmevent: MMEvent = await asyncify(data.session.query(self.alchemy.MMEvent).get, mmid)
            mmresponse: MMResponse = await asyncify(
                data.session.query(self.alchemy.MMResponse).filter_by(user=author, mmevent=mmevent).one_or_none)
            if mmresponse is None:
                mmresponse = self.alchemy.MMResponse(user=author, mmevent=mmevent, choice=choice)
                data.session.add(mmresponse)
            else:
                mmresponse.choice = choice
            await data.session_commit()
            await self._update_telegram_mm_message(client, mmevent)
            return f"✅ Messaggio ricevuto!"

        return callback

    def _gen_event_start_message(self, mmevent: MMEvent):
        text = f"🚩 L'evento [b]{mmevent.title}[/b] è iniziato!\n\n" \
               f"Partecipano:\n"
        for mmresponse in sorted(mmevent.responses, key=lambda mmr: mmr.user.username):
            if mmresponse.response == "YES":
                text += f"✅ {mmresponse.user}\n"
            elif mmresponse.response == "NO":
                text += f"❌ {mmresponse.user}\n"
        return text

    def _gen_unauth_message(self, user: User):
        return f"⚠️ Non sono autorizzato a mandare messaggi a [b]{user.username}[/b]!\n" \
               f"{user.telegram.mention()}, apri una chat privata con me e mandami un messaggio!"

    async def _run_mmevent(self, mmid: int):
        """Run a MMEvent."""
        # Open a new Alchemy Session
        session = self.alchemy.Session()
        # Find the MMEvent with the current session
        mmevent: MMEvent = await asyncify(session.query(self.alchemy.MMEvent).get, mmid)
        if mmevent is None:
            raise ValueError("Invalid mmid.")
        # Ensure the MMEvent hasn't already started
        if mmevent.datetime <= datetime.datetime.now():
            raise ValueError("MMEvent has already started.")
        # Ensure the MMEvent interface matches the current one
        if mmevent.interface != self.interface.name:
            raise ValueError("Invalid interface.")
        # If the matchmaking message hasn't been sent yet, do so now
        if mmevent.interface_data is None:
            if self.interface.name == "telegram":
                bot: TelegramBot = self.interface.bot
                client: PTBBot = bot.client
                # Build the Telegram keyboard
                # Send the keyboard
                message: PTBMessage = await self.interface.bot.safe_api_call(client.send_message,
                                                                             chat_id=self._mm_chat_id,
                                                                             text=telegram_escape(
                                                                                 self._gen_mm_message(mmevent)),
                                                                             parse_mode="HTML",
                                                                             disable_webpage_preview=True,
                                                                             reply_markup=self._gen_telegram_keyboard(
                                                                                 mmevent.mmid))
                # Store message data in the interface data object
                mmevent.interface_data = MMInterfaceDataTelegram(chat_id=self._mm_chat_id,
                                                                 message_id=message.message_id)
                await asyncify(session.commit)
            else:
                raise UnsupportedError()
        # Register handlers for the keyboard events
        if self.interface.name == "telegram":
            bot: TelegramBot = self.interface.bot
            client: PTBBot = bot.client
            self.interface.register_keyboard_key(f"mm{mmevent.mmid}_YES",
                                                 callback=self._gen_mm_telegram_callback(client, mmid, MMChoice.YES))
            self.interface.register_keyboard_key(f"mm{mmevent.mmid}_MAYBE",
                                                 callback=self._gen_mm_telegram_callback(client, mmid, MMChoice.MAYBE))
            self.interface.register_keyboard_key(f"mm{mmevent.mmid}_LATE_SHORT",
                                                 callback=self._gen_mm_telegram_callback(client, mmid,
                                                                                         MMChoice.LATE_SHORT))
            self.interface.register_keyboard_key(f"mm{mmevent.mmid}_LATE_MEDIUM",
                                                 callback=self._gen_mm_telegram_callback(client, mmid,
                                                                                         MMChoice.LATE_MEDIUM))
            self.interface.register_keyboard_key(f"mm{mmevent.mmid}_LATE_LONG",
                                                 callback=self._gen_mm_telegram_callback(client, mmid,
                                                                                         MMChoice.LATE_LONG))
            self.interface.register_keyboard_key(f"mm{mmevent.mmid}_NO_TIME",
                                                 callback=self._gen_mm_telegram_callback(client, mmid,
                                                                                         MMChoice.NO_TIME))
            self.interface.register_keyboard_key(f"mm{mmevent.mmid}_NO_INTEREST",
                                                 callback=self._gen_mm_telegram_callback(client, mmid,
                                                                                         MMChoice.NO_INTEREST))
            self.interface.register_keyboard_key(f"mm{mmevent.mmid}_NO_TECH",
                                                 callback=self._gen_mm_telegram_callback(client, mmid,
                                                                                         MMChoice.NO_TECH))
        else:
            raise UnsupportedError()
        # Sleep until the time of the event
        await sleep_until(mmevent.datetime)
        # Notify the positive answers of the event start
        if self.interface.name == "telegram":
            bot: TelegramBot = self.interface.bot
            client: PTBBot = bot.client
            for response in mmevent.responses:
                if response.choice == MMChoice.NO_INTEREST or response.choice == MMChoice.NO_TIME:
                    return
                try:
                    await self.interface.bot.safe_api_call(client.send_message,
                                                           chat_id=response.user.telegram.tg_id,
                                                           text=telegram_escape(self._gen_event_start_message(mmevent)),
                                                           parse_mode="HTML",
                                                           disable_webpage_preview=True)
                except Unauthorized:
                    await self.interface.bot.safe_api_call(client.send_message,
                                                           chat_id=self._mm_error_chat_id,
                                                           text=telegram_escape(
                                                               self._gen_unauth_message(response.user)),
                                                           parse_mode="HTML",
                                                           disable_webpage_preview=True)
        else:
            raise UnsupportedError()
        # Delete the event message
        if self.interface.name == "telegram":
            await self.interface.bot.safe_api_call(client.delete_message,
                                                   chat_id=mmevent.interface_data.chat_id,
                                                   message_id=mmevent.interface_data.message_id,
                                                   parse_mode="HTML",
                                                   disable_webpage_preview=True)
        # The end!
        await asyncify(session.close)
