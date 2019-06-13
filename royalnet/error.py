import typing
if typing.TYPE_CHECKING:
    from .network import ResponseError


class NoneFoundError(Exception):
    """The element that was being looked for was not found."""


class TooManyFoundError(Exception):
    """Multiple elements matching the request were found, and only one was expected."""


class UnregisteredError(Exception):
    """The command required a registered user, and the user was not registered."""


class UnsupportedError(Exception):
    """The command is not supported for the specified interface."""


class InvalidInputError(Exception):
    """The command has received invalid input and cannot complete."""


class InvalidConfigError(Exception):
    """The bot has not been configured correctly, therefore the command can not function."""


class RoyalnetRequestError(Exception):
    """An error was raised while handling the Royalnet request.

    This exception contains the :py:class:`royalnet.network.ResponseError` that was returned by the other Link."""
    def __init__(self, error: "ResponseError"):
        self.error: "ResponseError" = error


class RoyalnetResponseError(Exception):
    """The :py:class:`royalnet.network.Response` that was received is invalid."""


class ExternalError(Exception):
    """Something went wrong in a non-Royalnet component and the command execution cannot be completed."""


class FileTooBigError(Exception):
    """The file to be downloaded would be too big to store; therefore, it has been skipped."""


class CurrentlyDisabledError(Exception):
    """This feature is temporarely disabled and is not available right now."""
