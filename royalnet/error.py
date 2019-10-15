import typing
import royalherald as rh


class RoyalnetRequestError(Exception):
    """An error was raised while handling the Royalnet request.

    This exception contains the :py:class:`royalherald.ResponseFailure` that was returned by the other Link."""
    def __init__(self, error: rh.ResponseFailure):
        self.error: rh.ResponseFailure = error

    @property
    def args(self):
        return f"{self.error.name}", f"{self.error.description}", f"{self.error.extra_info}"


class RoyalnetResponseError(Exception):
    """The :py:class:`royalherald.Response` that was received is invalid."""
