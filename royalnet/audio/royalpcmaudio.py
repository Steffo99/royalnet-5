from discord import AudioSource
from discord.opus import Encoder as OpusEncoder
import typing
if typing.TYPE_CHECKING:
    from .royalpcmfile import RoyalPCMFile


class RoyalPCMAudio(AudioSource):
    def __init__(self, rpf: "RoyalPCMFile"):
        self.rpf: "RoyalPCMFile" = rpf
        self._file = open(rpf.audio_filename, "rb")

    def cleanup(self):
        self._file.close()

    def is_opus(self):
        return False

    def read(self):
        data: bytes = self._file.read(OpusEncoder.FRAME_SIZE)
        if len(data) != OpusEncoder.FRAME_SIZE:
            return b""
        return data

    def __repr__(self):
        return f"<RoyalPCMAudio {self.rpf.audio_filename}>"
