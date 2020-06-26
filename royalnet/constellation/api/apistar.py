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
    auth: Dict[str, bool] = {}
    deprecated: Dict[str, bool] = {}

    tags: List[str] = []
    __override__: List[str] = []

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
            elif method == "options":
                return api_success("Preflight allowed.", methods=self.methods())
            else:
                raise MethodNotImplementedError("Unknown method")
        except UnauthorizedError as e:
            return api_error(e, code=401, methods=self.methods())
        except NotFoundError as e:
            return api_error(e, code=404, methods=self.methods())
        except ForbiddenError as e:
            return api_error(e, code=403, methods=self.methods())
        except MethodNotImplementedError as e:
            return api_error(e, code=405, methods=self.methods())
        except BadRequestError as e:
            return api_error(e, code=400, methods=self.methods())
        except Exception as e:
            ru.sentry_exc(e)
            return api_error(e, code=500, methods=self.methods())
        else:
            return api_success(response, methods=self.methods())
        finally:
            await apidata.session_close()

    async def get(self, data: ApiData) -> ru.JSON:
        raise MethodNotImplementedError("GET is not implemented on this ApiStar")

    async def post(self, data: ApiData) -> ru.JSON:
        raise MethodNotImplementedError("POST is not implemented on this ApiStar")

    async def put(self, data: ApiData) -> ru.JSON:
        raise MethodNotImplementedError("PUT is not implemented on this ApiStar")

    async def delete(self, data: ApiData) -> ru.JSON:
        raise MethodNotImplementedError("DELETE is not implemented on this ApiStar")

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
            "summary": ru.strip_tabs(summary) if summary is not None else "",
            "description": ru.strip_tabs(description) if description is not None else "",
            "tags": self.tags,
            "deprecated": self.deprecated.get(method.__name__, False),
            "security": [{"RoyalnetLoginToken": ["logged_in"]}] if self.auth.get(method.__name__) else [],
            "parameters": [{
                "name": parameter_name,
                "in": "query",
                "description": ru.strip_tabs(self.parameters[method.__name__][parameter_name]),
                "schema": {},
            } for parameter_name in self.parameters.get(method.__name__, [])],
            "responses": {
                "200": {"description": "✅ OK!"},
                "400": {"description": "⚠️ Missing or invalid parameter."},
                "401": {"description": "⚠️ Invalid password."},
                "403": {"description": "⚠️ Missing or invalid token."},
                "404": {"description": "⚠️ Not found."},
                "405": {"description": "⚠️ Unsupported method."},
                "500": {"description": "⛔️ Serverside unhandled exception!"},
            }
        }

    @classmethod
    def methods(cls):
        magics = []
        for key, value in cls.__dict__.items():
            attr = value
            try:
                magic = attr.__magic__
            except AttributeError:
                continue
            if magic:
                magics.append(key)
        return [*magics, "options"]

    def swagger(self) -> ru.JSON:
        """Generate one or more swagger paths for this ApiStar."""
        result = {}
        for method in self.methods():
            if method not in ["get", "post", "put", "delete"]:
                continue
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
