from typing import Optional, AsyncGenerator, List, Tuple, Any, Dict
from royalnet.bard import UnsupportedError
from .fileaudiosource import FileAudioSource
from .ytdldiscord import YtdlDiscord

try:
    import discord
except ImportError:
    discord = None


class DiscordBard:
    """An abstract representation of a music sequence.

    Possible implementation may be playlist, song pools, multilayered tracks, and so on."""

    def __init__(self, voice_client: "discord.VoiceClient"):
        """Create manually a :class:`DiscordBard`.

        Warning:
            Avoid calling this method, please use :meth:`create` instead!"""
        self.voice_client: "discord.VoiceClient" = voice_client
        """The voice client that this :class:`DiscordBard` refers to."""

        self.now_playing: Optional[FileAudioSource] = None
        """The :class:`YtdlDiscord` that's currently being played."""

        self.generator: \
            AsyncGenerator[FileAudioSource, Tuple[Tuple[Any, ...], Dict[str, Any]]] = self._generator()
        """The AsyncGenerator responsible for deciding the next song that should be played."""

    async def _generator(self) -> AsyncGenerator[Optional[FileAudioSource], Tuple[Tuple[Any, ...], Dict[str, Any]]]:
        """Create an async generator that returns the next source to be played;
        it can take a args+kwargs tuple in input to optionally select a different source.

        The generator should ``yield`` once before doing anything else."""
        yield
        raise NotImplementedError()

    @classmethod
    async def create(cls, voice_client: "discord.VoiceClient") -> "DiscordBard":
        """Create an instance of the :class:`DiscordBard`, and initialize its async generator."""
        bard = cls(voice_client=voice_client)
        # noinspection PyTypeChecker
        none = await bard.generator.asend(None)
        assert none is None
        return bard

    async def next(self, *args, **kwargs) -> Optional[FileAudioSource]:
        """Get the next :class:`FileAudioSource` that should be played, and change :attr:`.now_playing`.

        Args and kwargs can be passed to the generator to select differently."""
        fas: Optional[FileAudioSource] = await self.generator.asend((args, kwargs,))
        self.now_playing = fas
        return fas

    async def stop(self):
        """Stop the playback of the current song."""
        if self.now_playing is not None:
            self.now_playing.stop()

    async def add(self, ytd: YtdlDiscord) -> None:
        """Add a new :class:`YtdlDiscord` to the :class:`DiscordBard`, if possible.

        Raises:
            UnsupportedError: If it isn't possible to add new :class:`YtdlDiscord` to the :class:`DiscordBard`.
        """
        raise UnsupportedError()

    async def peek(self) -> Optional[List[YtdlDiscord]]:
        """Return the contents of the :class:`DiscordBard` as a :class:`list`, if possible.

        Raises:
            UnsupportedError: If it isn't possible to display the :class:`DiscordBard` state as a :class:`list`.
        """
        raise UnsupportedError()

    async def remove(self, ytd: YtdlDiscord) -> None:
        """Remove a :class:`YtdlDiscord` from the :class:`DiscordBard`, if possible.

        Raises:
            UnsupportedError: If it isn't possible to remove the :class:`YtdlDiscord` from the :class:`DiscordBard`.
        """
        raise UnsupportedError()

    async def cleanup(self) -> None:
        """Enqueue the deletion of all :class:`YtdlDiscord` contained in the :class:`DiscordBard`, and return only once
        all deletions are complete."""
        raise NotImplementedError()

    async def length(self) -> int:
        """Return the length of the :class:`DiscordBard`.

        Raises:
            UnsupportedError: If :meth:`.peek` is unsupported."""
        return len(await self.peek())

