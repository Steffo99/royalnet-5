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


class PageStar(Star):
    """A PageStar is a class representing a single route of the website (for example, ``/api/user/get``).

    To create a new website route you should create a new class inheriting from this class with a function overriding
    :meth:`.page` and changing the values of :attr:`.path` and optionally :attr:`.methods`."""
    path: str = NotImplemented
    """The route of the star.
    
    Example:
        ::
        
            path: str = '/api/user/get'
        
    """

    methods: List[str] = ["GET"]
    """The HTTP methods supported by the Star, in form of a list.
    
    By default, a Star only supports the ``GET`` method, but more can be added.
    
    Example:
        ::
        
            methods: List[str] = ["GET", "POST", "PUT", "DELETE"]
            
    """

    def __repr__(self):
        return f"<{self.__class__.__qualname__}: {self.path}>"


class ExceptionStar(Star):
    """An ExceptionStar is a class that handles an :class:`Exception` raised by another star by returning a different
    response than the one originally intended.

    The handled exception type is specified in the :attr:`.error`.

    It can also handle standard webserver errors, such as ``404 Not Found``:
    to handle them, set :attr:`.error` to an :class:`int` of the corresponding error code.

    To create a new exception handler you should create a new class inheriting from this class with a function
    overriding :meth:`.page` and changing the value of :attr:`.error`."""
    error: Union[Type[Exception], int]
    """The error that should be handled by this star. It should be either a subclass of :exc:`Exception`, 
    or the :class:`int` of an HTTP error code.
    
    Examples:
        ::
        
            error: int = 404
            
        ::
        
            error: Type[Exception] = ValueError
    """

    def __repr__(self):
        return f"<{self.__class__.__qualname__}: handles {self.error}>"
