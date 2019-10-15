import contextlib
import os
import typing
import youtube_dl
from .ytdlinfo import YtdlInfo
from .errors import NotFoundError, MultipleFilesError, MissingInfoError, AlreadyDownloadedError


class YtdlFile:
    """Information about a youtube-dl downloaded file."""

    _default_ytdl_args = {
        "quiet": not __debug__,  # Do not print messages to stdout.
        "noplaylist": True,  # Download single video instead of a playlist if in doubt.
        "no_warnings": not __debug__,  # Do not print out anything for warnings.
        "outtmpl": "%(epoch)s-%(title)s-%(id)s.%(ext)s",  # Use the default outtmpl.
        "ignoreerrors": True  # Ignore unavailable videos
    }

    def __init__(self,
                 url: str,
                 info: typing.Optional[YtdlInfo] = None,
                 filename: typing.Optional[str] = None):
        self.url: str = url
        self.info: typing.Optional[YtdlInfo] = info
        self.filename: typing.Optional[str] = filename

    def has_info(self) -> bool:
        return self.info is not None

    def is_downloaded(self) -> bool:
        return self.filename is not None

    @contextlib.contextmanager
    def open(self):
        if not self.is_downloaded():
            raise FileNotFoundError("The file hasn't been downloaded yet.")
        with open(self.filename, "r") as file:
            yield file

    def update_info(self, **ytdl_args) -> None:
        infos = YtdlInfo.retrieve_for_url(self.url, **ytdl_args)
        if len(infos) == 0:
            raise NotFoundError()
        elif len(infos) > 1:
            raise MultipleFilesError()
        self.info = infos[0]

    def download_file(self, **ytdl_args) -> None:
        if not self.has_info():
            raise MissingInfoError()
        if self.is_downloaded():
            raise AlreadyDownloadedError()
        with youtube_dl.YoutubeDL({**self._default_ytdl_args, **ytdl_args}) as ytdl:
            filename = ytdl.prepare_filename(self.info.__dict__)
            ytdl.download([self.info.webpage_url])
            self.filename = filename

    def delete(self):
        if self.is_downloaded():
            os.remove(self.filename)
            self.filename = None

    @classmethod
    def download_from_url(cls, url: str, **ytdl_args) -> typing.List["YtdlFile"]:
        infos = YtdlInfo.retrieve_for_url(url, **ytdl_args)
        files = []
        for info in infos:
            file = YtdlFile(url=info.webpage_url, info=info)
            file.download_file(**ytdl_args)
            files.append(file)
        return files
