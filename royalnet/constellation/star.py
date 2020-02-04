from typing import *
from starlette.requests import Request
from starlette.responses import Response
from royalnet.commands import CommandInterface

if TYPE_CHECKING:
    from .constellation import Constellation


class Star:
    """A Star is a class representing a part of the website.

    It shouldn't be used directly: please use :class:`PageStar` and :class:`ExceptionStar` instead!"""
    def __init__(self, interface: CommandInterface):
        self.interface: CommandInterface = interface

    async def page(self, request: Request) -> Response:
        """The function generating the :class:`~starlette.Response` to a web :class:`~starlette.Request`.

        If it raises an error, the corresponding :class:`ExceptionStar` will be used to handle the request instead."""
        raise NotImplementedError()

    @property
    def constellation(self) -> "Constellation":
        """A shortcut for the :class:`Constellation`."""
        return self.interface.constellation

    @property
    def alchemy(self):
        """A shortcut for the :class:`~royalnet.alchemy.Alchemy` of the :class:`Constellation`."""
        return self.interface.constellation.alchemy

    # noinspection PyPep8Naming
    @property
    def Session(self):
        """A shortcut for the :class:`~royalnet.alchemy.Alchemy` :class:`Session` of the :class:`Constellation`."""
        return self.interface.constellation.alchemy.Session

    @property
    def session_acm(self):
        """A shortcut for :func:`.alchemy.session_acm` of the :class:`Constellation`."""
        return self.interface.constellation.alchemy.session_acm

    @property
    def config(self) -> Dict[str, Any]:
        """A shortcut for the Pack configuration of the :class:`Constellation`."""
        return self.interface.config

    def __repr__(self):
        return f"<{self.__class__.__qualname__}>"
