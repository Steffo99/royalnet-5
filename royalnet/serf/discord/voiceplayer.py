import asyncio
from typing import Optional
from .errors import *
from .playable import Playable
try:
    import discord
except ImportError:
    discord = None


class VoicePlayer:
    def __init__(self):
        self.voice_client: Optional["discord.VoiceClient"] = None
        self.playing: Optional[Playable] = None

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
        try:
            self.voice_client = await channel.connect()
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
        await self.voice_client.disconnect(force=True)
        self.voice_client = None

    async def move(self, channel: "discord.VoiceChannel"):
        """Move the :class:`VoicePlayer` to a different channel.

        This requires the :class:`VoicePlayer` to already be connected, and for the passed :class:`discord.VoiceChannel`
        to be in the same :class:`discord.Guild` as """
        if self.voice_client is None or not self.voice_client.is_connected():
            raise PlayerNotConnectedError()
        await self.voice_client.move_to(channel)

    async def start(self):
        """Start playing music on the :class:`discord.VoiceClient`."""
        if self.voice_client is None or not self.voice_client.is_connected():
            raise PlayerNotConnectedError()

    def _playback_ended(self, error=None):
        ...
