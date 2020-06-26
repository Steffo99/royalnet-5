from .apistar import ApiStar
from .jsonapi import api_response, api_success, api_error
from .apidata import ApiData
from .apierrors import \
    ApiError, \
    NotFoundError, \
    ForbiddenError, \
    BadRequestError, \
    ParameterError, \
    MissingParameterError, \
    InvalidParameterError, \
    MethodNotImplementedError, \
    UnsupportedError
from .magic import magic


__all__ = [
    "ApiStar",
    "api_response",
    "api_success",
    "api_error",
    "ApiData",
    "ApiError",
    "MissingParameterError",
    "NotFoundError",
    "ApiError",
    "NotFoundError",
    "ForbiddenError",
    "BadRequestError",
    "ParameterError",
    "MissingParameterError",
    "InvalidParameterError",
    "MethodNotImplementedError",
    "UnsupportedError",
    "magic",
]
