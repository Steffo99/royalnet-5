from discord import AudioSource
from discord.opus import Encoder as OpusEncoder
import typing
from .royalpcmfile import RoyalPCMFile


class RoyalPCMAudio(AudioSource):
    """A :py:class:`discord.AudioSource` that keeps data in a file instead of in memory."""

    def __init__(self, rpf: "RoyalPCMFile"):
        """Create a :py:class:`discord.audio.RoyalPCMAudio` from a :py:class:`royalnet.audio.RoyalPCMFile`.

        Warning:
            Not recommended, use :py:func:`royalnet.audio.RoyalPCMAudio.create_from_url` or :py:func:`royalnet.audio.RoyalPCMAudio.create_from_ytsearch` instead."""
        self.rpf: "RoyalPCMFile" = rpf
        self._file = open(self.rpf.audio_filename, "rb")

    @staticmethod
    def create_from_url(url: str) -> typing.List["RoyalPCMAudio"]:
        """Download a file with youtube_dl and create a list of RoyalPCMAudios.

        Parameters:
            url: The url of the file to download.

        Returns:
            A :py:class:`list` of RoyalPCMAudios, each corresponding to a downloaded video."""
        rpf_list = RoyalPCMFile.create_from_url(url)
        return [RoyalPCMAudio(rpf) for rpf in rpf_list]

    @staticmethod
    def create_from_ytsearch(search: str, amount: int = 1) -> typing.List["RoyalPCMAudio"]:
        """Search a string on YouTube and download the first ``amount`` number of videos, then download those with youtube_dl and create a list of RoyalPCMAudios.

        Parameters:
            search: The string to search on YouTube.
            amount: The number of videos to download.

        Returns:
            A :py:class:`list` of RoyalPCMAudios, each corresponding to a downloaded video."""
        rpf_list = RoyalPCMFile.create_from_ytsearch(search, amount)
        return [RoyalPCMAudio(rpf) for rpf in rpf_list]

    def is_opus(self):
        """This audio file isn't Opus-encoded, but PCM-encoded.
        
        Returns:
            ``False``."""
        return False

    def read(self):
        """Reads 20ms worth of audio.
        
        If the audio is complete, then returning an empty :py:class:`bytes`-like object to signal this is the way to do so."""
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
        """Permanently delete the downloaded file."""
        self._file.close()
        self.rpf.delete_audio_file()

    def __repr__(self):
        return f"<RoyalPCMAudio {self.rpf.audio_filename}>"
