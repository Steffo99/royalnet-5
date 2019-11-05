import royalnet
from starlette.requests import Request
from starlette.responses import *
from royalnet.web import PageStar


class VersionStar(PageStar):
    path = "/api/royalnet/version"

    async def page(self, request: Request, **kwargs) -> JSONResponse:
        return JSONResponse({
            "version": {
                "semantic": royalnet.version.semantic
            }
        })
