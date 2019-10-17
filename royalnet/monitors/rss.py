import typing
import feedparser
import asyncio
import datetime
from .monitor import Monitor
from ..utils import asyncify


class RssMonitor(Monitor):
    def __init__(self, url: str, interval: float, *, loop: asyncio.AbstractEventLoop):
        super().__init__(interval, loop=loop)
        self.url: str = url
        self._last_feed: feedparser.FeedParserDict = None

    @property
    def feed_title(self) -> typing.Optional[str]:
        if self._last_feed is None:
            return None
        return self._last_feed.feed.title

    @property
    def feed_link(self) -> typing.Optional[str]:
        if self._last_feed is None:
            return None
        return self._last_feed.feed.link

    @property
    def feed_description(self) -> typing.Optional[str]:
        if self._last_feed is None:
            return None
        return self._last_feed.feed.description

    @property
    def feed_published(self) -> typing.Optional[datetime.datetime]:
        if self._last_feed is None:
            return None
        return self._last_feed.feed.published_parsed

    async def check(self):
        self._last_feed = await asyncify(feedparser.parse, self.url)
        # TODO
        ...
