import typing
import discord
import re
import ffmpeg
from .ytdlfile import YtdlFile
from .fileaudiosource import FileAudioSource


class YtdlDiscord:
    def __init__(self, ytdl_file: YtdlFile):
        self.ytdl_file: YtdlFile = ytdl_file
        self.pcm_filename: typing.Optional[str] = None

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

    def to_audiosource(self) -> discord.AudioSource:
        stream = open(self.pcm_filename, "rb")
        return FileAudioSource(stream)
