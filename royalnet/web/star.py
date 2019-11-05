import typing
from starlette.requests import Request
from starlette.responses import Response
if typing.TYPE_CHECKING:
    from .constellation import Constellation


class Star:
    tables: set = {}

    def __init__(self, constellation: "Constellation"):
        self.constellation: "Constellation" = constellation

    async def page(self, request: Request, **kwargs) -> Response:
        raise NotImplementedError()


class PageStar(Star):
    path: str = NotImplemented

    methods: typing.List[str] = ["GET"]


class ExceptionStar(Star):
    error: typing.Union[typing.Type[Exception], int]
