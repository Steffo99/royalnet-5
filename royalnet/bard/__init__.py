from .ytdlinfo import YtdlInfo
from .ytdlfile import YtdlFile
from .ytdlmp3 import YtdlMp3
from .ytdldiscord import YtdlDiscord

try:
    from .fileaudiosource import FileAudioSource
except ImportError:
    FileAudioSource = None


__all__ = [
    "YtdlInfo",
    "YtdlFile",
    "YtdlMp3",
    "YtdlDiscord",
    "FileAudioSource",
]
