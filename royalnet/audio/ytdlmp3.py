import typing
import re
import ffmpeg
import os
from .ytdlinfo import YtdlInfo
from .ytdlfile import YtdlFile
from .fileaudiosource import FileAudioSource


class YtdlMp3:
    def __init__(self, ytdl_file: YtdlFile):
        self.ytdl_file: YtdlFile = ytdl_file
        self.mp3_filename: typing.Optional[str] = None
        self._fas_spawned: typing.List[FileAudioSource] = []

    def pcm_available(self):
        return self.mp3_filename is not None and os.path.exists(self.mp3_filename)

    def convert_to_mp3(self) -> None:
        if not self.ytdl_file.is_downloaded():
            raise FileNotFoundError("File hasn't been downloaded yet")
        destination_filename = re.sub(r"\.[^.]+$", ".mp3", self.ytdl_file.filename)
        out, err = (
            ffmpeg.input(self.ytdl_file.filename)
                  .output(destination_filename, format="mp3")
                  .overwrite_output()
                  .run_async()
        )
        self.mp3_filename = destination_filename

    def ready_up(self):
        if not self.ytdl_file.has_info():
            self.ytdl_file.update_info()
        if not self.ytdl_file.is_downloaded():
            self.ytdl_file.download_file()
        if not self.pcm_available():
            self.convert_to_mp3()

    def delete(self) -> None:
        if self.pcm_available():
            for source in self._fas_spawned:
                if not source.file.closed:
                    source.file.close()
            os.remove(self.mp3_filename)
            self.mp3_filename = None
        self.ytdl_file.delete()

    @classmethod
    def create_from_url(cls, url, **ytdl_args) -> typing.List["YtdlMp3"]:
        files = YtdlFile.download_from_url(url, **ytdl_args)
        dfiles = []
        for file in files:
            dfile = YtdlMp3(file)
            dfiles.append(dfile)
        return dfiles

    @classmethod
    def create_and_ready_from_url(cls, url, **ytdl_args) -> typing.List["YtdlMp3"]:
        dfiles = cls.create_from_url(url, **ytdl_args)
        for dfile in dfiles:
            dfile.ready_up()
        return dfiles

    @property
    def info(self) -> typing.Optional[YtdlInfo]:
        return self.ytdl_file.info
