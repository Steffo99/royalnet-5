"""The subpackage providing all classes related to music files.

It requires the ``bard`` extra to be installed (the :mod:`ffmpeg_python`, :mod:`youtube_dl` and :mod:`eyed3` packages).

You can install it with: ::

    pip install royalnet[bard]

"""

try:
    import ffmpeg
    import youtube_dl
    import eyed3
except ImportError:
    raise ImportError("The `bard` extra is not installed. Please install it with `pip install royalnet[bard]`.")

from .ytdlinfo import YtdlInfo
from .ytdlfile import YtdlFile
from .errors import BardError, YtdlError, NotFoundError, MultipleFilesError

__all__ = [
    "YtdlInfo",
    "YtdlFile",
    "BardError",
    "YtdlError",
    "NotFoundError",
    "MultipleFilesError",
]
