import typing
import re
import os
from royalnet.utils import asyncify, MultiLock
from .ytdlinfo import YtdlInfo
from .ytdlfile import YtdlFile

try:
    import ffmpeg
except ImportError:
    ffmpeg = None


class YtdlMp3:
    """A representation of a :class:`YtdlFile` conversion to mp3."""
    def __init__(self, ytdl_file: YtdlFile):
        self.ytdl_file: YtdlFile = ytdl_file
        self.mp3_filename: typing.Optional[str] = None
        self.lock: MultiLock = MultiLock()

    def __repr__(self):
        if not self.ytdl_file.has_info:
            return f"<{self.__class__.__qualname__} without info>"
        elif not self.ytdl_file.is_downloaded:
            return f"<{self.__class__.__qualname__} not downloaded>"
        elif not self.is_converted:
            return f"<{self.__class__.__qualname__} at '{self.ytdl_file.filename}' not converted>"
        else:
            return f"<{self.__class__.__qualname__} at '{self.mp3_filename}'>"

    @property
    def is_converted(self):
        """Has the file been converted?"""
        return self.mp3_filename is not None

    async def convert_to_mp3(self) -> None:
        """Convert the file to mp3 with :mod:`ffmpeg`."""
        if ffmpeg is None:
            raise ImportError("'bard' extra is not installed")
        await self.ytdl_file.download_file()
        if self.mp3_filename is None:
            async with self.ytdl_file.lock.normal():
                destination_filename = re.sub(r"\.[^.]+$", ".mp3", self.ytdl_file.filename)
                async with self.lock.exclusive():
                    await asyncify(
                        ffmpeg.input(self.ytdl_file.filename)
                              .output(destination_filename, format="mp3")
                              .overwrite_output()
                              .run
                    )
            self.mp3_filename = destination_filename

    async def delete_asap(self) -> None:
        """Delete the mp3 file."""
        if self.is_converted:
            async with self.lock.exclusive():
                os.remove(self.mp3_filename)
                self.mp3_filename = None

    @classmethod
    async def from_url(cls, url, **ytdl_args) -> typing.List["YtdlMp3"]:
        """Create a :class:`list` of :class:`YtdlMp3` from a URL."""
        files = await YtdlFile.from_url(url, **ytdl_args)
        dfiles = []
        for file in files:
            dfile = YtdlMp3(file)
            dfiles.append(dfile)
        return dfiles

    @property
    def info(self) -> typing.Optional[YtdlInfo]:
        """Shortcut to get the :class:`YtdlInfo` of the object."""
        return self.ytdl_file.info
