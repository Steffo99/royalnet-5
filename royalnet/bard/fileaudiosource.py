from typing import Optional
from .ytdlinfo import YtdlInfo

try:
    import discord
except ImportError:
    discord = None


class FileAudioSource(discord.AudioSource):
    """A :py:class:`discord.AudioSource` that uses a :py:class:`io.BufferedIOBase` as an input instead of memory.

    The stream should be in the usual PCM encoding.

    Warning:
        This AudioSource will consume (and close) the passed stream."""

    def __init__(self, file):
        """Create a FileAudioSource.

        Arguments:
            file: the file to be played back."""
        self.file = file

    def __repr__(self):
        if self.file.seekable():
            return f"<{self.__class__.__name__} @{self.file.tell()}>"
        else:
            return f"<{self.__class__.__name__}>"

    def is_opus(self):
        """This audio file isn't Opus-encoded, but PCM-encoded.

        Returns:
            ``False``."""
        return False

    def read(self):
        """Reads 20ms worth of audio.

        If the stream has ended, then return an empty :py:class:`bytes`-like object."""
        data: bytes = self.file.read(discord.opus.Encoder.FRAME_SIZE)
        # If there is no more data to be streamed
        if len(data) != discord.opus.Encoder.FRAME_SIZE:
            # Return that the stream has ended
            return b""
        return data
