from typing import *
from json import JSONDecodeError
from abc import *
from starlette.requests import Request
from starlette.responses import JSONResponse
from ..pagestar import PageStar
from .jsonapi import api_error, api_success
from .apidata import ApiData
from .apierrors import *


class ApiStar(PageStar, ABC):
    async def page(self, request: Request) -> JSONResponse:
        if request.query_params:
            data = request.query_params
        else:
            try:
                data = await request.json()
            except JSONDecodeError:
                data = {}
        try:
            response = await self.api(ApiData(data, self))
        except NotFoundError as e:
            return api_error(e, code=404)
        except ForbiddenError as e:
            return api_error(e, code=403)
        except NotImplementedError as e:
            return api_error(e, code=501)
        except ApiError as e:
            return api_error(e, code=400)
        except Exception as e:
            return api_error(e, code=500)
        return api_success(response)

    async def api(self, data: dict) -> dict:
        raise NotImplementedError()
