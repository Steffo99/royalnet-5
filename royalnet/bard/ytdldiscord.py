import typing
import re
import os
from contextlib import asynccontextmanager
from royalnet.utils import asyncify, MultiLock
from .ytdlinfo import YtdlInfo
from .ytdlfile import YtdlFile

try:
    from royalnet.bard.fileaudiosource import FileAudioSource
except ImportError:
    FileAudioSource = None

try:
    import ffmpeg
except ImportError:
    ffmpeg = None


class YtdlDiscord:
    """A representation of a YtdlFile conversion to the :mod:`discord` PCM format."""
    def __init__(self, ytdl_file: YtdlFile):
        self.ytdl_file: YtdlFile = ytdl_file
        self.pcm_filename: typing.Optional[str] = None
        self.lock: MultiLock = MultiLock()

    @property
    def is_converted(self):
        """Has the file been converted?"""
        return self.pcm_filename is not None

    async def convert_to_pcm(self) -> None:
        """Convert the file to pcm with :mod:`ffmpeg`."""
        if ffmpeg is None:
            raise ImportError("'bard' extra is not installed")
        await self.ytdl_file.download_file()
        if self.pcm_filename is None:
            async with self.ytdl_file.lock.normal():
                destination_filename = re.sub(r"\.[^.]+$", ".pcm", self.ytdl_file.filename)
                async with self.lock.exclusive():
                    await asyncify(
                        ffmpeg.input(self.ytdl_file.filename)
                              .output(destination_filename, format="s16le", ac=2, ar="48000")
                              .overwrite_output()
                              .run
                    )
            self.pcm_filename = destination_filename

    async def delete_asap(self) -> None:
        """Delete the mp3 file."""
        if self.is_converted:
            async with self.lock.exclusive():
                os.remove(self.pcm_filename)
                self.pcm_filename = None

    @classmethod
    async def from_url(cls, url, **ytdl_args) -> typing.List["YtdlDiscord"]:
        """Create a :class:`list` of :class:`YtdlMp3` from a URL."""
        files = await YtdlFile.from_url(url, **ytdl_args)
        dfiles = []
        for file in files:
            dfile = YtdlDiscord(file)
            dfiles.append(dfile)
        return dfiles

    @property
    def info(self) -> typing.Optional[YtdlInfo]:
        """Shortcut to get the :class:`YtdlInfo` of the object."""
        return self.ytdl_file.info

    @asynccontextmanager
    async def spawn_audiosource(self):
        if FileAudioSource is None:
            raise ImportError("'discord' extra is not installed")
        await self.convert_to_pcm()
        with open(self.pcm_filename, "rb") as stream:
            yield FileAudioSource(stream)
