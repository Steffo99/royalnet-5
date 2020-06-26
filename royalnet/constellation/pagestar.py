from typing import *
from .star import Star


class PageStar(Star):
    """A PageStar is a class representing a single route of the website (for example, ``/api/user/get``).

    To create a new website route you should create a new class inheriting from this class with a function overriding
    :meth:`.page`, :attr:`.path` and optionally :attr:`.methods`."""

    path: str = NotImplemented
    """The route of the star.

    Example:
        ::

            path: str = '/api/user/get'

    """

    @classmethod
    def methods(cls):
        """The HTTP methods supported by the Star, in form of a list.

        By default, a Star only supports the ``GET`` method, but more can be added.

        Example:
            ::

                methods: List[str] = ["GET", "POST", "PUT", "DELETE"]

        """
        return ["GET"]

    def __repr__(self):
        return f"<{self.__class__.__qualname__}: {self.path}>"
