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
        "quiet": True,  # Do not print messages to stdout.
        "noplaylist": True,  # Download single video instead of a playlist if in doubt.
        "no_warnings": True,  # Do not print out anything for warnings.,
        "format": "bestaudio"  # Fetch the best audio format available
    }

    def __init__(self, info: "YtdlInfo", **ytdl_args):
        super().__init__(info, outtmpl="%(title)s-%(id)s.%(ext)s", **ytdl_args)
        # Find the audio_filename with a regex (should be video.opus)
        self.audio_filename = re.sub(rf"\.{self.info.ext}$", ".opus", self.video_filename)
        # Convert the video to opus
        converter = ffmpeg.input(self.video_filename) \
                          .output(self.audio_filename)
        converter.run()
        # Delete the video file
        self.delete_video_file()

    @staticmethod
    def create_from_url(url, **ytdl_args) -> typing.List["RoyalAudioFile"]:
        info_list = YtdlInfo.create_from_url(url)
        return [RoyalAudioFile(info) for info in info_list]

    def delete_audio_file(self):
        # TODO: _might_ be unsafe, test this
        os.remove(self.audio_filename)

    def as_audio_source(self):
        return discord.FFmpegPCMAudio(self.audio_filename)
