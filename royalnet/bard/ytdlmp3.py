import typing
import re
import ffmpeg
import os
from .ytdlinfo import YtdlInfo
from .ytdlfile import YtdlFile
from royalnet.utils import asyncify, MultiLock


class YtdlMp3:
    """A representation of a YtdlFile conversion to mp3."""
    def __init__(self, ytdl_file: YtdlFile):
        self.ytdl_file: YtdlFile = ytdl_file
        self.mp3_filename: typing.Optional[str] = None
        self.lock: MultiLock = MultiLock()

    @property
    def is_converted(self):
        """Has the file been converted?"""
        return self.mp3_filename is not None

    async def convert_to_mp3(self) -> None:
        """Convert the file to mp3 with ``ffmpeg``."""
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

    def delete_asap(self) -> None:
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
