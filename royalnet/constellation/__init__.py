"""The part of :mod:`royalnet` that handles the webserver and webpages.

It uses many features of :mod:`starlette`."""

from .constellation import Constellation
from .star import Star, PageStar, ExceptionStar
from .shoot import shoot

__all__ = [
    "Constellation",
    "Star",
    "PageStar",
    "ExceptionStar",
    "shoot",
]
