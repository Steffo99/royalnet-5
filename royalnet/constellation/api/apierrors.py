class ApiError(Exception):
    pass


class NotFoundError(ApiError):
    pass


class ForbiddenError(ApiError):
    pass


class MissingParameterError(ApiError):
    pass


class NotImplementedError(ApiError):
    pass


class UnsupportedError(NotImplementedError):
    pass
