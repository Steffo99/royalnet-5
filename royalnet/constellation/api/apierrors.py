class ApiError(Exception):
    pass


class NotFoundError(ApiError):
    """404"""


class UnauthorizedError(ApiError):
    """401"""


class ForbiddenError(ApiError):
    """403"""


class BadRequestError(ApiError):
    """400"""


class ParameterError(BadRequestError):
    """400"""


class MissingParameterError(ParameterError):
    """400"""


class InvalidParameterError(ParameterError):
    """400"""


class MethodNotImplementedError(ApiError):
    """405"""


class UnsupportedError(MethodNotImplementedError):
    """405"""
