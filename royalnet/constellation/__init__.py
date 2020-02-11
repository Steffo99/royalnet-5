"""The subpackage providing all functions and classes that handle the webserver and the webpages.

It requires the ``constellation`` extra to be installed (:mod:`starlette`).

You can install it with: ::

    pip install royalnet[constellation]

It optionally uses the ``sentry`` extra for error reporting.

You can install them with: ::

    pip install royalnet[constellation,sentry]

"""

from .constellation import Constellation
from .star import Star
from .pagestar import PageStar

__all__ = [
    "Constellation",
    "Star",
    "PageStar",
]
