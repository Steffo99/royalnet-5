import typing
import discord
import re
import ffmpeg
import os
from .ytdlfile import YtdlFile
from .fileaudiosource import FileAudioSource


class YtdlDiscord:
    def __init__(self, ytdl_file: YtdlFile):
        self.ytdl_file: YtdlFile = ytdl_file
        self.pcm_filename: typing.Optional[str] = None

    def pcm_available(self):
        return self.pcm_filename is not None and os.path.exists(self.pcm_filename)

    def convert_to_pcm(self) -> None:
        if not self.ytdl_file.is_downloaded():
            raise FileNotFoundError("File hasn't been downloaded yet")
        destination_filename = re.sub(r"\.[^.]+$", ".pcm", self.ytdl_file.filename)
        (
            ffmpeg.input(self.ytdl_file.filename)
                  .output(destination_filename, format="s16le", ac=2, ar="48000")
                  .overwrite_output()
                  .run(quiet=True)
        )
        self.pcm_filename = destination_filename

    def ready_up(self):
        if not self.ytdl_file.has_info():
            self.ytdl_file.update_info()
        if not self.ytdl_file.is_downloaded():
            self.ytdl_file.download_file()
        if not self.pcm_available():
            self.convert_to_pcm()

    def to_audiosource(self) -> discord.AudioSource:
        if not self.pcm_available():
            raise FileNotFoundError("File hasn't been converted to PCM yet")
        stream = open(self.pcm_filename, "rb")
        return FileAudioSource(stream)

    def delete(self) -> None:
        if self.pcm_available():
            os.remove(self.pcm_filename)
            self.pcm_filename = None
        self.ytdl_file.delete()
