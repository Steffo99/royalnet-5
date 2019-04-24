from ..error import RoyalnetError


class Message:
    """A message sent through the Royalnet."""
    def __repr__(self):
        return f"<{self.__class__.__name__}>"


class IdentifySuccessfulMessage(Message):
    """The Royalnet identification step was successful."""


class ServerErrorMessage(Message):
    """Something went wrong in the connection to the :py:class:`royalnet.network.RoyalnetServer`."""
    def __init__(self, reason):
        super().__init__()
        self.reason = reason


class InvalidSecretEM(ServerErrorMessage):
    """The sent secret was incorrect.

     This message terminates connection to the :py:class:`royalnet.network.RoyalnetServer`."""


class InvalidPackageEM(ServerErrorMessage):
    """The sent :py:class:`royalnet.network.Package` was invalid."""


class InvalidDestinationEM(InvalidPackageEM):
    """The :py:class:`royalnet.network.Package` destination was invalid or not found."""


class Reply(Message):
    """A reply to a request sent through the Royalnet."""

    def raise_on_error(self) -> None:
        """If the reply is an error, raise an error, otherwise, do nothing.

        Raises:
            A :py:exc:`RoyalnetError`, if the Reply is an error, otherwise, nothing."""
        raise NotImplementedError()


class RequestSuccessful(Reply):
    """The sent request was successful."""

    def raise_on_error(self) -> None:
        """If the reply is an error, raise an error, otherwise, do nothing.

        Does nothing."""
        pass


class RequestError(Reply):
    """The sent request wasn't successful."""

    def __init__(self, exc: Exception):
        """Create a RequestError.

        Parameters:
             exc: The exception that caused the error in the request."""
        self.exc: Exception = exc

    def raise_on_error(self) -> None:
        """If the reply is an error, raise an error, otherwise, do nothing.

        Raises:
            Always raises a :py:exc:`royalnet.error.RoyalnetError`, containing the exception that caused the error."""
        raise RoyalnetError(exc=self.exc)
