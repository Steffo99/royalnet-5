import discord
import ffmpeg
import re
import os
import typing
import logging as _logging
from .youtubedl import YtdlFile, YtdlInfo

log = _logging.getLogger(__name__)


class RoyalAudioFile(YtdlFile):
    ytdl_args = {
        "logger": log,  # Log messages to a logging.Logger instance.
        "format": "bestaudio"  # Fetch the best audio format available
    }

    def __init__(self, info: "YtdlInfo", **ytdl_args):
        # Overwrite the new ytdl_args
        self.ytdl_args = {**self.ytdl_args, **ytdl_args}
        log.info(f"Now downloading {info.webpage_url}")
        super().__init__(info, outtmpl="./downloads/%(title)s-%(id)s.ytdl", **self.ytdl_args)
        # Find the audio_filename with a regex (should be video.opus)
        log.info(f"Preparing {self.video_filename}...")
        # Convert the video to opus
        # Actually not needed, but we do this anyways for compression reasons
        ffmpeg.input(self.video_filename) \
              .output(self.audio_filename, format="s16le", acodec="pcm_s16le", ac=2, ar="48000") \
              .overwrite_output() \
              .run(quiet=not __debug__)
        # Delete the video file
        log.info(f"Deleting {self.video_filename}")
        self.delete_video_file()

    @staticmethod
    def create_from_url(url, **ytdl_args) -> typing.List["RoyalAudioFile"]:
        info_list = YtdlInfo.create_from_url(url)
        return [RoyalAudioFile(info) for info in info_list]

    @property
    def audio_filename(self):
        return f"./downloads/{self.info.title}-{self.info.id}.pcm"

    def as_audio_source(self):
        # TODO: find a way to close this
        file = open(self.audio_filename, "rb")
        return discord.PCMAudio(file)

    def delete_audio_file(self):
        # TODO: _might_ be unsafe, test this
        os.remove(self.audio_filename)
