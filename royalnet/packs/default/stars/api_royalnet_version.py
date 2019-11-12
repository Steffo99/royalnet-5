import royalnet
from starlette.requests import Request
from starlette.responses import *
from royalnet.web import PageStar


class ApiRoyalnetVersionStar(PageStar):
    path = "/api/royalnet/version"

    async def page(self, request: Request) -> JSONResponse:
        return JSONResponse({
            "version": {
                "semantic": royalnet.version.semantic
            }
        })
