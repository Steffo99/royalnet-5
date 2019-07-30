class YtdlError(Exception):
    pass


class NotFoundError(YtdlError):
    pass


class MultipleFilesError(YtdlError):
    pass


class MissingInfoError(YtdlError):
    pass


class AlreadyDownloadedError(YtdlError):
    pass
