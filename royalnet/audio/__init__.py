"""Video and audio downloading related classes, mainly used for Discord voice bots."""

from .playmodes import PlayMode, Playlist, Pool
from .youtubedl import YtdlFile, YtdlInfo
from .royalpcmfile import RoyalPCMFile
from .royalpcmaudio import RoyalPCMAudio

__all__ = ["PlayMode", "Playlist", "Pool", "YtdlFile", "YtdlInfo", "RoyalPCMFile", "RoyalPCMAudio"]
