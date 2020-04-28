import typing
import re
import os
import logging
import ffmpeg
import discord
from contextlib import asynccontextmanager
from royalnet.utils import asyncify, MultiLock
from royalnet.bard import YtdlInfo, YtdlFile
from .fileaudiosource import FileAudioSource

log = logging.getLogger(__name__)


class YtdlDiscord:
    """A representation of a :class:`YtdlFile` conversion to the :mod:`discord` PCM format."""

    def __init__(self, ytdl_file: YtdlFile):
        self.ytdl_file: YtdlFile = ytdl_file
        self.pcm_filename: typing.Optional[str] = None
        self.lock: MultiLock = MultiLock()

    def __repr__(self):
        if not self.ytdl_file.has_info:
            return f"<{self.__class__.__qualname__} without info>"
        elif not self.ytdl_file.is_downloaded:
            return f"<{self.__class__.__qualname__} not downloaded>"
        elif not self.is_converted:
            return f"<{self.__class__.__qualname__} at '{self.ytdl_file.filename}' not converted>"
        else:
            return f"<{self.__class__.__qualname__} at '{self.pcm_filename}'>"

    @property
    def is_converted(self):
        """Has the file been converted?"""
        return self.pcm_filename is not None

    async def convert_to_pcm(self) -> None:
        """Convert the file to pcm with :mod:`ffmpeg`."""
        await self.ytdl_file.download_file()
        if self.pcm_filename is None:
            async with self.ytdl_file.lock.normal():
                destination_filename = re.sub(r"\.[^.]+$", ".pcm", self.ytdl_file.filename)
                async with self.lock.exclusive():
                    log.debug(f"Converting to PCM: {self.ytdl_file.filename}")
                    out, err = await asyncify(
                        ffmpeg.input(self.ytdl_file.filename)
                              .output(destination_filename, format="s16le", ac=2, ar="48000")
                              .overwrite_output()
                              .run,
                        capture_stdout=True,
                        capture_stderr=True,
                    )
                    log.debug(f"ffmpeg returned: ({type(out)}, {type(err)})")
            self.pcm_filename = destination_filename

    async def delete_asap(self) -> None:
        """Delete the mp3 file."""
        log.debug(f"Trying to delete: {self}")
        if self.is_converted:
            async with self.lock.exclusive():
                os.remove(self.pcm_filename)
                log.debug(f"Deleted: {self.pcm_filename}")
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
        log.debug(f"Spawning audio_source for: {self}")
        await self.convert_to_pcm()
        async with self.lock.normal():
            with open(self.pcm_filename, "rb") as stream:
                fas = FileAudioSource(stream)
                yield fas

    def embed(self) -> "discord.Embed":
        """Return this info as a :py:class:`discord.Embed`."""
        colors = {
            "youtube": 0xCC0000,
            "soundcloud": 0xFF5400,
            "Clyp": 0x3DBEB3,
            "Bandcamp": 0x1DA0C3,
            "PeerTube": 0xF1680D,
            "generic": 0x4F545C,
        }
        embed = discord.Embed(title=self.info.title,
                              colour=discord.Colour(colors.get(self.info.extractor, 0x4F545C)),
                              url=self.info.webpage_url if (self.info.webpage_url and self.info.webpage_url.startswith("http")) else discord.embeds.EmptyEmbed)
        if self.info.thumbnail:
            embed.set_thumbnail(url=self.info.thumbnail)
        if self.info.uploader:
            embed.set_author(name=self.info.uploader,
                             url=self.info.uploader_url if self.info.uploader_url is not None else discord.embeds.EmptyEmbed)
        elif self.info.artist:
            embed.set_author(name=self.info.artist,
                             url=discord.embeds.EmptyEmbed)
        if self.info.album:
            embed.add_field(name="Album", value=self.info.album, inline=True)
        if self.info.duration:
            embed.add_field(name="Duration", value=str(self.info.duration), inline=True)
        if self.info.extractor != "generic" and self.info.upload_date:
            embed.add_field(name="Published on", value=self.info.upload_date.strftime("%d %b %Y"), inline=True)
        # embed.set_footer(text="Source: youtube-dl", icon_url="https://i.imgur.com/TSvSRYn.png")
        return embed
