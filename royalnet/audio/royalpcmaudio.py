from discord import AudioSource
from discord.opus import Encoder as OpusEncoder
import typing
from .royalpcmfile import RoyalPCMFile


class RoyalPCMAudio(AudioSource):
    def __init__(self, rpf: "RoyalPCMFile"):
        self.rpf: "RoyalPCMFile" = rpf
        self._file = open(self.rpf.audio_filename, "rb")

    @staticmethod
    def create_from_url(url: str) -> typing.List["RoyalPCMAudio"]:
        rpf_list = RoyalPCMFile.create_from_url(url)
        return [RoyalPCMAudio(rpf) for rpf in rpf_list]

    @staticmethod
    def create_from_ytsearch(search: str, amount: int = 1) -> typing.List["RoyalPCMAudio"]:
        rpf_list = RoyalPCMFile.create_from_ytsearch(search, amount)
        return [RoyalPCMAudio(rpf) for rpf in rpf_list]

    def is_opus(self):
        return False

    def read(self):
        data: bytes = self._file.read(OpusEncoder.FRAME_SIZE)
        # If the file was externally closed, it means it was deleted
        if self._file.closed:
            return b""
        if len(data) != OpusEncoder.FRAME_SIZE:
            # Close the file as soon as the playback is finished
            self._file.close()
            # Reopen the file, so it can be reused
            self._file = open(self.rpf.audio_filename, "rb")
            return b""
        return data

    def delete(self):
        self._file.close()
        self.rpf.delete_audio_file()

    def __repr__(self):
        return f"<RoyalPCMAudio {self.rpf.audio_filename}>"
