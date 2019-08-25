"""Video and audio downloading related classes, mainly used for Discord voice bots."""

from . import playmodes
from .ytdlinfo import YtdlInfo
from .ytdlfile import YtdlFile
from .fileaudiosource import FileAudioSource
from .ytdldiscord import YtdlDiscord
from .ytdlmp3 import YtdlMp3

__all__ = ["playmodes", "YtdlInfo", "YtdlFile", "FileAudioSource", "YtdlDiscord", "YtdlMp3"]
