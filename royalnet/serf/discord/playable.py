import logging
from typing import Optional, AsyncGenerator, Tuple, Any, Dict
try:
    import discord
except ImportError:
    discord = None


log = logging.getLogger(__name__)


class Playable:
    """An abstract class representing something that can be played back in a :class:`VoicePlayer`."""
    def __init__(self):
        """Create a :class:`Playable`.

        Warning:
            Avoid using this method, as it does not initialize the generator! Use :meth:`.create` instead."""
        log.debug("Creating a Playable...")
        self.generator: Optional[AsyncGenerator[Optional["discord.AudioSource"],
                                                Tuple[Tuple[Any, ...], Dict[str, Any]]]] = self._generator()

    # PyCharm doesn't like what I'm doing here.
    # noinspection PyTypeChecker
    @classmethod
    async def create(cls, *args, **kwargs):
        """Create a :class:`Playable` and initialize its generator."""
        playable = cls(*args, **kwargs)
        log.debug("Sending None to the generator...")
        await playable.generator.asend(None)
        log.debug("Playable ready!")
        return playable

    async def next(self, *args, **kwargs) -> Optional["discord.AudioSource"]:
        """Get the next :class:`discord.AudioSource` that should be played.

        Called when the :class:`Playable` is first attached to a :class:`VoicePlayer` and when a
        :class:`discord.AudioSource` stops playing.

        Args and kwargs can be used to pass data to the generator.

        Returns:
             :const:`None` if there is nothing available to play, otherwise the :class:`discord.AudioSource` that should
             be played.
        """
        log.debug("Getting next AudioSource...")
        audio_source: Optional["discord.AudioSource"] = await self.generator.asend((args, kwargs,))
        log.debug(f"Next: {audio_source}")
        return audio_source

    async def _generator(self) \
            -> AsyncGenerator[Optional["discord.AudioSource"], Tuple[Tuple[Any, ...], Dict[str, Any]]]:
        """Create an async generator that returns the next source to be played;
        it can take a args+kwargs tuple in input to optionally select a different source.

        Note:
            For `weird Python reasons
            <https://www.python.org/dev/peps/pep-0525/#support-for-asynchronous-iteration-protocol>`, the generator
            should ``yield`` once before doing anything else."""
        yield
        raise NotImplementedError()

    async def destroy(self):
        """Clean up the Playable, as it is about to be replaced or deleted."""
        raise NotImplementedError()
