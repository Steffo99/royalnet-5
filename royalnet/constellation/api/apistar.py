from typing import *
from json import JSONDecodeError
from abc import *
from starlette.requests import Request
from starlette.responses import JSONResponse
from ..pagestar import PageStar
from .jsonapi import api_error, api_success
from .apidata import ApiData
from .apierrors import *
import royalnet.utils as ru
import logging
import re

log = logging.getLogger(__name__)


class ApiStar(PageStar, ABC):
    parameters: Dict[str, Dict[str, str]] = {}

    tags: List[str] = []

    deprecated: bool = False

    async def page(self, request: Request) -> JSONResponse:
        if request.query_params:
            data = request.query_params
        else:
            try:
                data = await request.json()
            except JSONDecodeError:
                data = {}
        apidata = ApiData(data=data, star=self)

        method = request.method.lower()

        try:
            if method == "get":
                response = await self.get(apidata)
            elif method == "post":
                response = await self.post(apidata)
            elif method == "put":
                response = await self.put(apidata)
            elif method == "delete":
                response = await self.delete(apidata)
            else:
                raise MethodNotImplementedError("Unknown method")
        except UnauthorizedError as e:
            return api_error(e, code=401)
        except NotFoundError as e:
            return api_error(e, code=404)
        except ForbiddenError as e:
            return api_error(e, code=403)
        except MethodNotImplementedError as e:
            return api_error(e, code=501)
        except BadRequestError as e:
            return api_error(e, code=400)
        except Exception as e:
            ru.sentry_exc(e)
            return api_error(e, code=500)
        else:
            return api_success(response)
        finally:
            await apidata.session_close()

    async def get(self, data: ApiData) -> ru.JSON:
        raise MethodNotImplementedError()

    async def post(self, data: ApiData) -> ru.JSON:
        raise MethodNotImplementedError()

    async def put(self, data: ApiData) -> ru.JSON:
        raise MethodNotImplementedError()

    async def delete(self, data: ApiData) -> ru.JSON:
        raise MethodNotImplementedError()

    def __swagger_for_a_method(self, method: Callable) -> ru.JSON:
        docstring = method.__doc__ or ""
        if docstring is None:
            log.error("Python was started with -OO, so docstrings are disabled and a summary can't be generated.")
            summary = ""
            description = ""
        else:
            summary, description = re.match(r"^(.*)(?:\n{2,}((?:.|\n)*))?", docstring).groups()

        return {
            "operationId": f"{self.__class__.__name__}_{method.__name__}",
            "summary": ru.strip_tabs(summary) if summary is not None else None,
            "description": ru.strip_tabs(description) if description is not None else None,
            "tags": self.tags,
            "security": [{"RoyalnetLoginToken": ["logged_in"]}],
            "parameters": [{
                "name": parameter_name,
                "in": "query",
                "description": ru.strip_tabs(self.parameters[method.__name__][parameter_name]),
                "type": "string",
            } for parameter_name in self.parameters.get(method.__name__, [])]
        }

    def swagger(self) -> ru.JSON:
        """Generate one or more swagger paths for this ApiStar."""
        result = {}
        for method in self.methods:
            result[method.lower()] = self.__swagger_for_a_method(self.__getattribute__(method.lower()))
        return result

        # result = {}
        # for method in cls.methods:
        #     result[method.lower()] = {
        #         "operationId": cls.__name__,
        #         "summary": cls.summary,
        #         "description": cls.description,
        #         "responses": {
        #             "200": {"description": "Success"},
        #             "400": {"description": "Bad request"},
        #             "403": {"description": "Forbidden"},
        #             "404": {"description": "Not found"},
        #             "500": {"description": "Serverside unhandled exception"},
        #             "501": {"description": "Not yet implemented"}
        #         },
        #         "tags": cls.tags,
        #         "parameters": [{
        #             "name": parameter,
        #             "in": "query",
        #             "description": cls.parameters[parameter],
        #             "type": "string"
        #         } for parameter in cls.parameters]
        #     }
        #     if cls.requires_auth:
        #         result[method.lower()]["security"] = [{"RoyalnetLoginToken": ["logged_in"]}]
        # return result
