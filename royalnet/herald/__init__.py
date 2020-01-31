"""The subpackage providing all functions and classes to handle communication between process (even over the Internet).

It is based on :mod:`websockets`.

It requires the ``herald`` extra to be installed.

You can install it with: ::

    pip install royalnet[herald]

"""

from .config import Config
from .errors import *
from .link import Link
from .package import Package
from .request import Request
from .response import Response, ResponseSuccess, ResponseFailure
from .server import Server
from .broadcast import Broadcast


__all__ = [
    "Config",
    "HeraldError",
    "ConnectionClosedError",
    "LinkError",
    "InvalidServerResponseError",
    "ServerError",
    "Link",
    "Package",
    "Request",
    "Response",
    "ResponseSuccess",
    "ResponseFailure",
    "Server",
    "Broadcast",
]
