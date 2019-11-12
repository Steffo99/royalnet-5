class BardError(Exception):
    """Base class for ``bard`` errors."""


class YtdlError(BardError):
    """Base class for ``youtube_dl`` errors."""


class NotFoundError(YtdlError):
    """The requested resource wasn't found."""


class MultipleFilesError(YtdlError):
    """The resource contains multiple media files."""
