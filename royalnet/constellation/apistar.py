from typing import *
from json import JSONDecodeError
from abc import *
from starlette.requests import Request
from starlette.responses import JSONResponse
from .pagestar import PageStar
from .jsonapi import api_error, api_success


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
            response = await self.api(data)
        except Exception as e:
            return api_error(e)
        return api_success(response)

    async def api(self, data: dict) -> dict:
        raise NotImplementedError()
