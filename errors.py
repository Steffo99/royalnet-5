class NotFoundError(Exception):
    pass


class AlreadyExistingError(Exception):
    pass


class DurationError(Exception):
    pass


class InfoNotRetrievedError(Exception):
    pass


class FileNotDownloadedError(Exception):
    pass


class AlreadyDownloadedError(Exception):
    pass


class InvalidConfigError(Exception):
    pass


class VideoHasNoName(Exception):
    pass


class VideoInfoExtractionFailed(Exception):
    pass


class VideoIsPlaylist(Exception):
    pass


class VideoInfoUnknown(Exception):
    pass


class VideoIsNotReady(Exception):
    pass


class PrivateError(Exception):
    pass
