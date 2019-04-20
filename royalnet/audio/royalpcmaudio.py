from discord import AudioSource
from discord.opus import Encoder as OpusEncoder
import typing
from .royalpcmfile import RoyalPCMFile


class RoyalPCMAudio(AudioSource):
    def __init__(self, rpf: "RoyalPCMFile"):
        self.rpf: "RoyalPCMFile" = rpf
        self._file = open(rpf.audio_filename, "rb")

    @staticmethod
    def create_from_url(url) -> typing.List["RoyalPCMAudio"]:
        rpf_list = RoyalPCMFile.create_from_url(url)
        return [RoyalPCMAudio(rpf) for rpf in rpf_list]

    def is_opus(self):
        return False

    def read(self):
        data: bytes = self._file.read(OpusEncoder.FRAME_SIZE)
        if len(data) != OpusEncoder.FRAME_SIZE:
            return b""
        return data

    def __repr__(self):
        return f"<RoyalPCMAudio {self.rpf.audio_filename}>"

    def __del__(self):
        self._file.close()
        del self.rpf
