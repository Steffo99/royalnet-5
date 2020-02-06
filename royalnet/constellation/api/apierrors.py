class ApiError(Exception):
    pass


class NotFoundException(ApiError):
    pass


class UnauthorizedException(ApiError):
    pass


class MissingParameterException(ApiError):
    pass
