import ffmpeg
import os
import typing
import time
from .youtubedl import YtdlFile, YtdlInfo


class RoyalPCMFile(YtdlFile):
    ytdl_args = {
        "format": "bestaudio"  # Fetch the best audio format available
    }

    def __init__(self, info: "YtdlInfo", **ytdl_args):
        # Preemptively initialize info to be able to generate the filename
        self.info = info
        # Set the time to generate the filename
        self._time = time.time()
        # Ensure the file doesn't already exist
        if os.path.exists(self._ytdl_filename) or os.path.exists(self.audio_filename):
            raise FileExistsError("Can't overwrite file")
        # Overwrite the new ytdl_args
        self.ytdl_args = {**self.ytdl_args, **ytdl_args}
        self.ytdl_args["log"].info(f"Now downloading {info.webpage_url}")
        super().__init__(info, outtmpl=self._ytdl_filename, **self.ytdl_args)
        # Find the audio_filename with a regex (should be video.opus)
        self.ytdl_args["log"].info(f"Preparing {self.video_filename}...")
        # Convert the video to pcm
        ffmpeg.input(f"./{self.video_filename}") \
              .output(self.audio_filename, format="s16le", ac=2, ar="48000") \
              .overwrite_output() \
              .run(quiet=False)
        # Delete the video file
        self.ytdl_args["log"].info(f"Deleting {self.video_filename}")
        self.delete_video_file()

    def __repr__(self):
        return f"<RoyalPCMFile {self.audio_filename}>"

    @staticmethod
    def create_from_url(url, **ytdl_args) -> typing.List["RoyalPCMFile"]:
        info_list = YtdlInfo.create_from_url(url)
        return [RoyalPCMFile(info) for info in info_list]

    @property
    def _ytdl_filename(self):
        return f"./downloads/{self.info.title}-{str(int(self._time))}.ytdl"

    @property
    def audio_filename(self):
        return f"./downloads/{self.info.title}-{str(int(self._time))}.pcm"

    def __del__(self):
        self.ytdl_args["log"].info(f"Deleting {self.audio_filename}")
        os.remove(self.audio_filename)
