from ..errors import SerfError


class DiscordSerfError(SerfError):
    """Base class for all :mod:`royalnet.serf.discord` errors."""


class VoicePlayerError(DiscordSerfError):
    """Base class for all :class:`VoicePlayer` errors."""


class AlreadyConnectedError(VoicePlayerError):
    """Base class for the "Already Connected" errors."""


class PlayerAlreadyConnectedError(AlreadyConnectedError):
    """The :class:`VoicePlayer` is already connected to voice.

    Access the :class:`discord.VoiceClient` through :attr:`VoicePlayer.voice_client`!"""


class GuildAlreadyConnectedError(AlreadyConnectedError):
    """The :class:`discord.Client` is already connected to voice in a channel of this guild."""


class OpusNotLoadedError(VoicePlayerError):
    """The Opus library hasn't been loaded `as required
    <https://discordpy.readthedocs.io/en/latest/api.html#discord.VoiceClient>` by :mod:`discord`."""


class DiscordTimeoutError(VoicePlayerError):
    """The websocket didn't get a response from the Discord voice servers in time."""


class PlayerNotConnectedError(VoicePlayerError):
    """The :class:`VoicePlayer` isn't connected to the Discord voice servers.

    Use :meth:`VoicePlayer.connect` first!"""


class PlayerAlreadyPlaying(VoicePlayerError):
    """The :class:`VoicePlayer` is already playing audio and cannot start playing audio again."""
