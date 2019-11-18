class BardError(Exception):
    """Base class for :mod:`bard` errors."""


class YtdlError(BardError):
    """Base class for errors caused by :mod:`youtube_dl`."""


class NotFoundError(YtdlError):
    """The requested resource wasn't found."""


class MultipleFilesError(YtdlError):
    """The resource contains multiple media files."""


class UnsupportedError(BardError):
    """The method you tried to call on a :class:`DiscordBard` is not supported on that particular Bard."""
