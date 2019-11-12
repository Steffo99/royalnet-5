class HeraldError(Exception):
    """A generic :py:mod:`royalherald` error."""


class LinkError(HeraldError):
    """An error for something that happened in a :py:class:`Link`."""


class ServerError(HeraldError):
    """An error for something that happened in a :py:class:`Server`."""


class ConnectionClosedError(LinkError):
    """The :py:class:`Link`'s connection was closed unexpectedly. The link can't be used anymore."""


class InvalidServerResponseError(LinkError):
    """The :py:class:`Server` sent invalid data to the :py:class:`Link`."""
