from typing import Optional, AsyncGenerator, List, Tuple, Any, Dict
from .ytdldiscord import YtdlDiscord
from .fileaudiosource import FileAudioSource
from .errors import UnsupportedError


class DiscordBard:
    """An abstract representation of a music sequence.

    Possible implementation may be playlist, song pools, multilayered tracks, and so on."""

    def __init__(self):
        """Create manually a :class:`DiscordBard`.

        Warning:
            Avoid calling this method, please use :meth:`create` instead!"""
        self.now_playing: Optional[YtdlDiscord] = None
        """The :class:`YtdlDiscord` that's currently being played."""

        self.generator: \
            AsyncGenerator[FileAudioSource, Tuple[Tuple[Any, ...], Dict[str, Any]]] = self._generate_generator()
        """The AsyncGenerator responsible for deciding the next song that should be played."""

    async def _generate_generator(self) -> AsyncGenerator[FileAudioSource, Tuple[Tuple[Any, ...], Dict[str, Any]]]:
        """Create an async generator that returns the next source to be played;
        it can take a args+kwargs tuple in input to optionally select a different source.

        The generator should ``yield`` once before doing anything else."""
        args, kwargs = yield
        raise NotImplementedError()

    @classmethod
    async def create(cls) -> "DiscordBard":
        """Create an instance of the :class:`DiscordBard`, and initialize its async generator."""
        bard = cls()
        # noinspection PyTypeChecker
        none = bard.generator.asend(None)
        assert none is None
        return bard

    async def next(self, *args, **kwargs) -> Optional[FileAudioSource]:
        """Get the next :class:`FileAudioSource` that should be played, and change :attr:`.now_playing`.

        Args and kwargs can be passed to the generator to select differently."""
        fas: Optional[FileAudioSource] = await self.generator.asend((args, kwargs))
        self.now_playing = fas
        return fas

    async def add(self, ytd: YtdlDiscord):
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

    async def remove(self, ytd: YtdlDiscord):
        """Remove a :class:`YtdlDiscord` from the :class:`DiscordBard`, if possible.

        Raises:
            UnsupportedError: If it isn't possible to remove the :class:`YtdlDiscord` from the :class:`DiscordBard`.
        """
        raise UnsupportedError()

    async def cleanup(self):
        """Enqueue the deletion of all :class:`YtdlDiscord` contained in the :class:`DiscordBard`, and return only once
        all deletions are complete."""
        raise NotImplementedError()
