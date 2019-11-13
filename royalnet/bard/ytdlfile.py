import os
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from royalnet.utils import asyncify, MultiLock
from asyncio import AbstractEventLoop, get_event_loop
from .ytdlinfo import YtdlInfo
from .errors import NotFoundError, MultipleFilesError

try:
    from youtube_dl import YoutubeDL
except ImportError:
    youtube_dl = None


class YtdlFile:
    """A representation of a file download with ``youtube_dl``."""

    default_ytdl_args = {
        "quiet": not __debug__,  # Do not print messages to stdout.
        "noplaylist": True,  # Download single video instead of a playlist if in doubt.
        "no_warnings": not __debug__,  # Do not print out anything for warnings.
        "outtmpl": "%(epoch)s-%(title)s-%(id)s.%(ext)s",  # Use the default outtmpl.
        "ignoreerrors": True  # Ignore unavailable videos
    }

    def __init__(self,
                 url: str,
                 info: Optional[YtdlInfo] = None,
                 filename: Optional[str] = None,
                 ytdl_args: Optional[Dict[str, Any]] = None,
                 loop: Optional[AbstractEventLoop] = None):
        """Create a YtdlFile instance.

        Warning:
            Please avoid using directly ``__init__()``, use :meth:`.from_url` instead!"""
        self.url: str = url
        self.info: Optional[YtdlInfo] = info
        self.filename: Optional[str] = filename
        self.ytdl_args: Dict[str, Any] = {**self.default_ytdl_args, **ytdl_args}
        self.lock: MultiLock = MultiLock()
        if not loop:
            loop = get_event_loop()
        self._loop = loop

    @property
    def has_info(self) -> bool:
        """Does the YtdlFile have info available?"""
        return self.info is not None

    async def retrieve_info(self) -> None:
        """Retrieve info about the YtdlFile through ``youtube_dl``."""
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
        if YoutubeDL is None:
            raise ImportError("'bard' extra is not installed")

        def download():
            """Download function block to be asyncified."""
            with YoutubeDL(self.ytdl_args) as ytdl:
                filename = ytdl.prepare_filename(self.info.__dict__)
                ytdl.download([self.info.webpage_url])
                self.filename = filename

        await self.retrieve_info()
        async with self.lock.exclusive():
            await asyncify(download, loop=self._loop)

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
            with open(self.filename, "rb") as file:
                yield file

    async def delete_asap(self):
        """As soon as nothing is using the file, delete it."""
        async with self.lock.exclusive():
            os.remove(self.filename)
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
