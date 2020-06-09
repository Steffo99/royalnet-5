import asyncio
import threading
import logging
from typing import Optional
from .errors import *
from .playable import Playable
from ...utils import sentry_exc
try:
    import discord
except ImportError:
    discord = None

log = logging.getLogger(__name__)


class VoicePlayer:
    def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop] = None):
        self.voice_client: Optional["discord.VoiceClient"] = None
        self.playing: Optional[Playable] = None
        if loop is None:
            self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        else:
            self.loop = loop
        self._playback_ended_event: threading.Event = threading.Event()

    async def connect(self, channel: "discord.VoiceChannel") -> "discord.VoiceClient":
        """Connect the :class:`VoicePlayer` to a :class:`discord.VoiceChannel`, creating a :class:`discord.VoiceClient`
        that handles the connection.

        Args:
            channel: The :class:`discord.VoiceChannel` to connect into.

        Returns:
            The created :class:`discord.VoiceClient`.
            (It will be stored in :attr:`VoicePlayer.voice_client` anyways!)

        Raises:
            PlayerAlreadyConnectedError:
            DiscordTimeoutError:
            GuildAlreadyConnectedError:
            OpusNotLoadedError:
        """
        if self.voice_client is not None and self.voice_client.is_connected():
            raise PlayerAlreadyConnectedError()
        log.debug(f"Connecting to: {channel}")
        try:
            self.voice_client = await channel.connect(reconnect=False, timeout=3)
        except asyncio.TimeoutError:
            raise DiscordTimeoutError()
        except discord.ClientException:
            raise GuildAlreadyConnectedError()
        except discord.opus.OpusNotLoaded:
            raise OpusNotLoadedError()
        return self.voice_client

    async def disconnect(self) -> None:
        """Disconnect the :class:`VoicePlayer` from the channel where it is currently connected, and set
        :attr:`.voice_client` to :const:`None`.

        Raises:
            PlayerNotConnectedError:
        """
        if self.voice_client is None or not self.voice_client.is_connected():
            raise PlayerNotConnectedError()
        log.debug(f"Disconnecting...")
        await self.voice_client.disconnect(force=True)
        self.voice_client = None

    async def move(self, channel: "discord.VoiceChannel"):
        """Move the :class:`VoicePlayer` to a different channel.

        This requires the :class:`VoicePlayer` to already be connected, and for the passed :class:`discord.VoiceChannel`
        to be in the same :class:`discord.Guild` of the :class:`VoicePlayer`."""
        if self.voice_client is None or not self.voice_client.is_connected():
            raise PlayerNotConnectedError()
        if self.voice_client.guild != channel.guild:
            raise ValueError("Can't move between two guilds.")
        log.debug(f"Moving to: {channel}")
        await self.voice_client.move_to(channel)

    async def start(self):
        """Start playing music on the :class:`discord.VoiceClient`.

        Info:
            Doesn't pass any ``*args`` or ``**kwargs`` to the :class:`Playable`.
        """
        if self.voice_client is None or not self.voice_client.is_connected():
            raise PlayerNotConnectedError()
        if self.voice_client.is_playing():
            raise PlayerAlreadyPlayingError()
        log.debug("Getting next AudioSource...")
        next_source: Optional["discord.AudioSource"] = await self.playing.next()
        if next_source is None:
            log.debug(f"Next source would be None, stopping here...")
            return
        log.debug(f"Next: {next_source}")
        try:
            self.voice_client.play(next_source, after=self._playback_ended)
        except discord.ClientException as e:
            sentry_exc(e)
            await self.disconnect()
        self.loop.create_task(self._playback_check())

    async def _playback_check(self):
        while True:
            if self._playback_ended_event.is_set():
                self._playback_ended_event.clear()
                await self.start()
                break
            await asyncio.sleep(1)

    def _playback_ended(self, error=None):
        if error is not None:
            sentry_exc(error)
            return
        self._playback_ended_event.set()

    async def change_playing(self, value: Playable):
        await self.playing.destroy()
        self.playing = value
