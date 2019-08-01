import typing
import re
import ffmpeg
import os
from .ytdlinfo import YtdlInfo
from .ytdlfile import YtdlFile
from .fileaudiosource import FileAudioSource


class YtdlVorbis:
    def __init__(self, ytdl_file: YtdlFile):
        self.ytdl_file: YtdlFile = ytdl_file
        self.vorbis_filename: typing.Optional[str] = None
        self._fas_spawned: typing.List[FileAudioSource] = []

    def pcm_available(self):
        return self.vorbis_filename is not None and os.path.exists(self.vorbis_filename)

    def convert_to_vorbis(self) -> None:
        if not self.ytdl_file.is_downloaded():
            raise FileNotFoundError("File hasn't been downloaded yet")
        destination_filename = re.sub(r"\.[^.]+$", ".mp3", self.ytdl_file.filename)
        out, err = (
            ffmpeg.input(self.ytdl_file.filename)
                  .output(destination_filename, format="mp3")
                  .overwrite_output()
                  .run()
        )
        self.vorbis_filename = destination_filename

    def ready_up(self):
        if not self.ytdl_file.has_info():
            self.ytdl_file.update_info()
        if not self.ytdl_file.is_downloaded():
            self.ytdl_file.download_file()
        if not self.pcm_available():
            self.convert_to_vorbis()

    def delete(self) -> None:
        if self.pcm_available():
            for source in self._fas_spawned:
                if not source.file.closed:
                    source.file.close()
            os.remove(self.vorbis_filename)
            self.vorbis_filename = None
        self.ytdl_file.delete()

    @classmethod
    def create_from_url(cls, url, **ytdl_args) -> typing.List["YtdlVorbis"]:
        files = YtdlFile.download_from_url(url, **ytdl_args)
        dfiles = []
        for file in files:
            dfile = YtdlVorbis(file)
            dfiles.append(dfile)
        return dfiles

    @classmethod
    def create_and_ready_from_url(cls, url, **ytdl_args) -> typing.List["YtdlVorbis"]:
        dfiles = cls.create_from_url(url, **ytdl_args)
        for dfile in dfiles:
            dfile.ready_up()
        return dfiles

    @property
    def info(self) -> typing.Optional[YtdlInfo]:
        return self.ytdl_file.info
