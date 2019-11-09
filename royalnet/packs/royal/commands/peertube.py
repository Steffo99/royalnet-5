import aiohttp
import asyncio
import datetime
import logging
import dateparser
from royalnet.commands import *
from royalnet.utils import telegram_escape


log = logging.getLogger(__name__)


class PeertubeCommand(Command):
    name: str = "peertube"

    description: str = "Guarda quando è uscito l'ultimo video su RoyalTube."

    _url = r"https://pt.steffo.eu/feeds/videos.json?sort=-publishedAt&filter=local"

    _ready = asyncio.Event()

    _timeout = 300

    _latest_date: datetime.datetime = None

    _telegram_group_id = -1001153723135

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        if self.interface.name == "telegram":
            self.loop.create_task(self._ready_up())
            self.loop.create_task(self._update())

    async def _get_json(self):
        log.debug("Getting jsonfeed")
        async with aiohttp.ClientSession() as session:
            async with session.get(self._url) as response:
                log.debug("Parsing jsonfeed")
                j = await response.json()
                log.debug("Jsonfeed parsed successfully")
        return j

    async def _send(self, message):
        client = self.interface.bot.client
        await self.interface.bot.safe_api_call(client.send_message,
                                               chat_id=self._telegram_group_id,
                                               text=telegram_escape(message),
                                               parse_mode="HTML",
                                               disable_webpage_preview=True)

    async def _ready_up(self):
        j = await self._get_json()
        if j["version"] != "https://jsonfeed.org/version/1":
            raise ConfigurationError("_url is not a jsonfeed")
        videos = j["items"]
        for video in reversed(videos):
            date_modified = dateparser.parse(video["date_modified"])
            if self._latest_date is None or date_modified > self._latest_date:
                log.debug(f"Found newer video: {date_modified}")
                self._latest_date = date_modified
        self._ready.set()

    async def _update(self):
        await self._ready.wait()
        while True:
            j = await self._get_json()
            videos = j["items"]
            for video in reversed(videos):
                date_modified = dateparser.parse(video["date_modified"])
                if date_modified > self._latest_date:
                    log.debug(f"Found newer video: {date_modified}")
                    self._latest_date = date_modified
                    await self._send(f"🆕 Nuovo video su RoyalTube!\n"
                                     f"[b]{video['title']}[/b]\n"
                                     f"{video['url']}")
            await asyncio.sleep(self._timeout)

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        if self.interface.name != "telegram":
            raise UnsupportedError()
        await data.reply(f"ℹ️ Ultimo video caricato il: [b]{self._latest_date.isoformat()}[/b]")
