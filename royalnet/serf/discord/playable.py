from typing import Optional, AsyncGenerator, Tuple, Any, Dict
try:
    import discord
except ImportError:
    discord = None


class Playable:
    """An abstract class representing something that can be played back in a :class:`VoicePlayer`."""
    def __init__(self):
        self.generator: \
            Optional[AsyncGenerator[Optional["discord.AudioSource"], Tuple[Tuple[Any, ...], Dict[str, Any]]]] = None

    async def next(self, *args, **kwargs) -> Optional["discord.AudioSource"]:
        """Get the next :class:`discord.AudioSource` that should be played.

        Called when the :class:`Playable` is first attached to a :class:`VoicePlayer` and when a
        :class:`discord.AudioSource` stops playing.

        Args and kwargs can be used to pass data to the generator.

        Returns:
             :const:`None` if there is nothing available to play, otherwise the :class:`discord.AudioSource` that should
             be played.
        """
        return await self.generator.asend((args, kwargs,))

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
