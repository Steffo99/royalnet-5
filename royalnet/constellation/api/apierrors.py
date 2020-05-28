class ApiError(Exception):
    pass


class NotFoundError(ApiError):
    pass


class UnauthorizedError(ApiError):
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


class MethodNotImplementedError(ApiError):
    pass


class UnsupportedError(MethodNotImplementedError):
    pass
