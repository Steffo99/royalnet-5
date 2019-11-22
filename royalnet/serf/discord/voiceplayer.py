import asyncio
from typing import Optional
from .errors import *
try:
    import discord
except ImportError:
    discord = None


class VoicePlayer:
    def __init__(self):
        self.voice_client: Optional["discord.VoiceClient"] = None
        ...

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
        if self.voice_client is not None:
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
        if self.voice_client is None:
            raise PlayerNotConnectedError()
        await self.voice_client.disconnect(force=True)
        self.voice_client = None

    async def move(self, channel: "discord.VoiceChannel"):
        """Move the :class:`VoicePlayer` to a different channel.

        This requires the :class:`VoicePlayer` to already be connected, and for the passed :class:`discord.VoiceChannel`
        to be in the same :class:`discord.Guild` as """

    ...
