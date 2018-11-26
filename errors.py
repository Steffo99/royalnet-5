class RequestError(Exception):
    pass


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
