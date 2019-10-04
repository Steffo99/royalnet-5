import typing
if typing.TYPE_CHECKING:
    from .network import ResponseError


class RoyalnetRequestError(Exception):
    """An error was raised while handling the Royalnet request.

    This exception contains the :py:class:`royalnet.network.ResponseError` that was returned by the other Link."""
    def __init__(self, error: "ResponseError"):
        self.error: "ResponseError" = error

    @property
    def args(self):
        return f"{self.error.name}", f"{self.error.description}", f"{self.error.extra_info}"


class RoyalnetResponseError(Exception):
    """The :py:class:`royalnet.network.Response` that was received is invalid."""
