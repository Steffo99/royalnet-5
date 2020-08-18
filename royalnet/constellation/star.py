import abc
from typing import *

from starlette.requests import Request
from starlette.responses import Response

if TYPE_CHECKING:
    from .constellation import Constellation
    from ..commands import ConfigDict
    from ..alchemy import Alchemy
    import sqlalchemy.orm.session


class Star(metaclass=abc.ABCMeta):
    """A Star is a class representing a part of the website.

    It shouldn't be used directly: please use :class:`PageStar` and :class:`ExceptionStar` instead!"""

    def __init__(self, constellation: "Constellation", config: "ConfigDict"):
        self.constellation: "Constellation" = constellation
        self.config: "ConfigDict" = config

    @abc.abstractmethod
    async def page(self, request: Request) -> Response:
        """The function generating the :class:`~starlette.Response` to a web :class:`~starlette.Request`.

        If it raises an error, the corresponding :class:`ExceptionStar` will be used to handle the request instead."""
        raise NotImplementedError()

    @property
    def alchemy(self) -> "Alchemy":
        """A shortcut for the :class:`~royalnet.alchemy.Alchemy` of the :class:`Constellation`."""
        return self.constellation.alchemy

    # noinspection PyPep8Naming
    @property
    def Session(self) -> "sqlalchemy.orm.session.Session":
        """A shortcut for the :class:`~royalnet.alchemy.Alchemy` :class:`Session` of the :class:`Constellation`."""
        return self.constellation.alchemy.Session

    @property
    def session_acm(self):
        """A shortcut for :func:`.alchemy.session_acm` of the :class:`Constellation`."""
        return self.constellation.alchemy.session_acm

    def __repr__(self):
        return f"<{self.__class__.__qualname__}>"
