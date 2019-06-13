import logging
import ffmpeg
import os
import typing
import time
import datetime
from .youtubedl import YtdlFile, YtdlInfo
from ..error import FileTooBigError
from ..utils import fileformat


log = logging.getLogger(__name__)


class RoyalPCMFile(YtdlFile):
    ytdl_args = {
        "format": "bestaudio"  # Fetch the best audio format available
    }

    def __init__(self, info: "YtdlInfo", **ytdl_args):
        # Preemptively initialize info to be able to generate the filename
        self.info = info
        # If the video is longer than 3 hours, don't download it
        if self.info.duration >= datetime.timedelta(hours=3):
            raise FileTooBigError("File is over 3 hours long")
        # Set the time to generate the filename
        self._time = time.time()
        # Ensure the file doesn't already exist
        if os.path.exists(self.ytdl_filename) or os.path.exists(self.audio_filename):
            raise FileExistsError("Can't overwrite file")
        # Overwrite the new ytdl_args
        self.ytdl_args = {**self.ytdl_args, **ytdl_args}
        log.info(f"Now downloading {info.webpage_url}")
        super().__init__(info, outtmpl=self.ytdl_filename, **self.ytdl_args)
        # Find the audio_filename with a regex (should be video.opus)
        log.info(f"Converting {self.video_filename}...")
        # Convert the video to pcm
        try:
            ffmpeg.input(f"./{self.video_filename}") \
                  .output(self.audio_filename, format="s16le", ac=2, ar="48000") \
                  .overwrite_output() \
                  .run(quiet=True)
        except ffmpeg.Error as exc:
            log.error(f"FFmpeg error: {exc.stderr}")
            raise
        # Delete the video file
        log.info(f"Deleting {self.video_filename}")
        self.delete_video_file()

    def __repr__(self):
        return f"<RoyalPCMFile {self.audio_filename}>"

    @staticmethod
    def create_from_url(url: str, **ytdl_args) -> typing.List["RoyalPCMFile"]:
        """Download a file with youtube_dl and create a list of :py:class:`discord.audio.RoyalPCMFile`.

        Parameters:
            url: The url of the file to download.
            ytdl_args: Extra arguments to be passed to YoutubeDL while downloading.

        Returns:
            A :py:class:`list` of RoyalPCMAudios, each corresponding to a downloaded video."""
        info_list = YtdlInfo.create_from_url(url)
        return [RoyalPCMFile(info, **ytdl_args) for info in info_list]

    @staticmethod
    def create_from_ytsearch(search: str, amount: int = 1, **ytdl_args) -> typing.List["RoyalPCMFile"]:
        """Search a string on YouTube and download the first ``amount`` number of videos, then download those with youtube_dl and create a list of :py:class:`discord.audio.RoyalPCMFile`.

        Parameters:
            search: The string to search on YouTube.
            amount: The number of videos to download.
            ytdl_args: Extra arguments to be passed to YoutubeDL while downloading.

        Returns:
            A :py:class:`list` of RoyalPCMFiles, each corresponding to a downloaded video."""
        url = f"ytsearch{amount}:{search}"
        info_list = YtdlInfo.create_from_url(url)
        return [RoyalPCMFile(info, **ytdl_args) for info in info_list]

    @property
    def ytdl_filename(self) -> str:
        """
        Returns:
            The name of the downloaded video file, as a :py:class:`str`.

        Warning:
            It's going to be deleted as soon as the :py:func:`royalnet.audio.RoyalPCMFile.__init__` function has completed, so it's probably not going to be very useful...
        """
        return f"./downloads/{fileformat(self.info.title)}-{fileformat(str(int(self._time)))}.ytdl"

    @property
    def audio_filename(self) -> str:
        """
        Returns:
            The name of the downloaded and PCM-converted audio file."""
        return f"./downloads/{fileformat(self.info.title)}-{fileformat(str(int(self._time)))}.pcm"

    def delete_audio_file(self):
        """Delete the PCM-converted audio file."""
        log.info(f"Deleting {self.audio_filename}")
        os.remove(self.audio_filename)
