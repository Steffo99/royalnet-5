import os
import logging
import re
import eyed3
from contextlib import asynccontextmanager
from typing import *
from royalnet.utils import *
from asyncio import AbstractEventLoop, get_event_loop
from .ytdlinfo import YtdlInfo
from .errors import NotFoundError, MultipleFilesError
from youtube_dl import YoutubeDL


log = logging.getLogger(__name__)


class YtdlFile:
    """A representation of a file download with `youtube_dl <https://ytdl-org.github.io/youtube-dl/index.html>`_."""

    default_ytdl_args = {
        "quiet": not __debug__,  # Do not print messages to stdout.
        "noplaylist": True,  # Download single video instead of a playlist if in doubt.
        "no_warnings": not __debug__,  # Do not print out anything for warnings.
        "outtmpl": "./downloads/%(epoch)s-%(title)s-%(id)s.%(ext)s",  # Use the default outtmpl.
        "ignoreerrors": True  # Ignore unavailable videos
    }

    def __init__(self,
                 url: str,
                 info: Optional[YtdlInfo] = None,
                 filename: Optional[str] = None,
                 ytdl_args: Optional[Dict[str, Any]] = None,
                 loop: Optional[AbstractEventLoop] = None):
        """Create a :class:`YtdlFile` instance.

        Warning:
            Please avoid using directly :meth:`.__init__`, use :meth:`.from_url` instead!"""
        self.url: str = url
        self.info: Optional[YtdlInfo] = info
        self.filename: Optional[str] = filename
        self.ytdl_args: Dict[str, Any] = {**self.default_ytdl_args, **ytdl_args}
        self.lock: MultiLock = MultiLock()
        if not loop:
            loop = get_event_loop()
        self._loop = loop

    def __repr__(self):
        if not self.has_info:
            return f"<{self.__class__.__qualname__} without info>"
        elif not self.is_downloaded:
            return f"<{self.__class__.__qualname__} not downloaded>"
        else:
            return f"<{self.__class__.__qualname__} at '{self.filename}'>"

    @property
    def has_info(self) -> bool:
        """Does the :class:`YtdlFile` have info available?"""
        return self.info is not None

    async def retrieve_info(self) -> None:
        """Retrieve info about the :class:`YtdlFile` through :class:`YoutubeDL`."""
        if not self.has_info:
            infos = await asyncify(YtdlInfo.from_url, self.url, loop=self._loop, **self.ytdl_args)
            if len(infos) == 0:
                raise NotFoundError()
            elif len(infos) > 1:
                raise MultipleFilesError()
            self.info = infos[0]

    @property
    def is_downloaded(self) -> bool:
        """Has the file been downloaded yet?"""
        return self.filename is not None

    async def download_file(self) -> None:
        """Download the file."""
        def download():
            """Download function block to be asyncified."""
            with YoutubeDL(self.ytdl_args) as ytdl:
                filename = ytdl.prepare_filename(self.info.__dict__)
            with YoutubeDL({**self.ytdl_args, "outtmpl": filename}) as ytdl:
                ytdl.download([self.info.webpage_url])
            # "WARNING: Requested formats are incompatible for merge and will be merged into mkv."
            if not os.path.exists(filename):
                filename = re.sub(r"\.[^.]+$", ".mkv", filename)
            self.filename = filename

        await self.retrieve_info()
        if not self.is_downloaded:
            async with self.lock.exclusive():
                log.debug(f"Downloading with youtube-dl: {self}")
                await asyncify(download, loop=self._loop)
                if self.info.extractor == "generic":
                    log.debug(f"Generic extractor detected, updating info from the downloaded file: {self}")
                    self.set_ytdlinfo_from_id3_tags()

    def set_ytdlinfo_from_id3_tags(self):
        tag_file = eyed3.load(self.filename)
        if not tag_file:
            log.debug(f"No ID3 tags found: {self}")
            return
        tag: eyed3.core.Tag = tag_file.tag
        if tag.title:
            log.debug(f"Found title: {self}")
            self.info.title = tag.title
        if tag.album:
            log.debug(f"Found album: {self}")
            self.info.album = tag.album
        if tag.artist:
            log.debug(f"Found artist: {self}")
            self.info.artist = tag.artist

    @asynccontextmanager
    async def aopen(self):
        """Open the downloaded file as an async context manager (and download it if it isn't available yet).

        Example:
            You can use the async context manager like this: ::

                async with ytdlfile.aopen() as file:
                    b: bytes = file.read()

        """
        await self.download_file()
        async with self.lock.normal():
            log.debug(f"File opened: {self.filename}")
            with open(self.filename, "rb") as file:
                yield file
            log.debug(f"File closed: {self.filename}")

    async def delete_asap(self):
        """As soon as nothing is using the file, delete it."""
        log.debug(f"Trying to delete: {self.filename}")
        if self.filename is not None:
            async with self.lock.exclusive():
                os.remove(self.filename)
                log.debug(f"Deleted: {self.filename}")
                self.filename = None

    @classmethod
    async def from_url(cls, url: str, **ytdl_args) -> List["YtdlFile"]:
        """Create a :class:`list` of :class:`YtdlFile` from a URL."""
        infos = await YtdlInfo.from_url(url, **ytdl_args)
        files = []
        for info in infos:
            file = YtdlFile(url=info.webpage_url, info=info, ytdl_args=ytdl_args)
            files.append(file)
        return files
