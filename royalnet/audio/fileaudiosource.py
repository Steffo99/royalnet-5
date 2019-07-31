import discord


class FileAudioSource(discord.AudioSource):
    """A :py:class:`discord.AudioSource` that uses a :py:class:`io.BufferedIOBase` as an input instead of memory.

    The stream should be in the usual PCM encoding.

    Warning:
        This AudioSource will consume (and close) the passed stream."""

    def __init__(self, file):
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

        If the audio is complete, then returning an empty :py:class:`bytes`-like object to signal this is the way to do so."""
        # If the stream is closed, it should stop playing immediatly
        if self.file.closed:
            return b""
        data: bytes = self.file.read(discord.opus.Encoder.FRAME_SIZE)
        # If there is no more data to be streamed
        if len(data) != discord.opus.Encoder.FRAME_SIZE:
            # Close the file
            self.file.close()
            return b""
        return data
