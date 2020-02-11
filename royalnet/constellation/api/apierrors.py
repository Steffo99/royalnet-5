class ApiError(Exception):
    pass


class NotFoundError(ApiError):
    pass


class ForbiddenError(ApiError):
    pass


class BadRequestError(ApiError):
    pass


class ParameterError(BadRequestError):
    pass


class MissingParameterError(ParameterError):
    pass


class InvalidParameterError(ParameterError):
    pass


class NotImplementedError(ApiError):
    pass


class UnsupportedError(NotImplementedError):
    pass
