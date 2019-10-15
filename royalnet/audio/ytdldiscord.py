import typing
import re
import ffmpeg
import os
from .ytdlinfo import YtdlInfo
from .ytdlfile import YtdlFile
from .fileaudiosource import FileAudioSource


class YtdlDiscord:
    def __init__(self, ytdl_file: YtdlFile):
        self.ytdl_file: YtdlFile = ytdl_file
        self.pcm_filename: typing.Optional[str] = None
        self._fas_spawned: typing.List[FileAudioSource] = []

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.info.title or 'Unknown Title'} ({'ready' if self.pcm_available() else 'not ready'}," \
               f" {len(self._fas_spawned)} audiosources spawned)>"

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
                  .run(quiet=not __debug__)
        )
        self.pcm_filename = destination_filename

    def ready_up(self):
        if not self.ytdl_file.has_info():
            self.ytdl_file.update_info()
        if not self.ytdl_file.is_downloaded():
            self.ytdl_file.download_file()
        if not self.pcm_available():
            self.convert_to_pcm()

    def spawn_audiosource(self) -> FileAudioSource:
        if not self.pcm_available():
            raise FileNotFoundError("File hasn't been converted to PCM yet")
        stream = open(self.pcm_filename, "rb")
        source = FileAudioSource(stream)
        # FIXME: it's a intentional memory leak
        self._fas_spawned.append(source)
        return source

    def delete(self) -> None:
        if self.pcm_available():
            for source in self._fas_spawned:
                if not source.file.closed:
                    source.file.close()
            os.remove(self.pcm_filename)
            self.pcm_filename = None
        self.ytdl_file.delete()

    @classmethod
    def create_from_url(cls, url, **ytdl_args) -> typing.List["YtdlDiscord"]:
        files = YtdlFile.download_from_url(url, **ytdl_args)
        dfiles = []
        for file in files:
            dfile = YtdlDiscord(file)
            dfiles.append(dfile)
        return dfiles

    @property
    def info(self) -> typing.Optional[YtdlInfo]:
        return self.ytdl_file.info
