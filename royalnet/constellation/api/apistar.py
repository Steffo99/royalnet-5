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


class ApiStar(PageStar, ABC):
    summary: str = ""

    description: str = ""

    parameters: Dict[str, str] = {}

    tags: List[str] = []

    requires_auth: bool = False

    async def page(self, request: Request) -> JSONResponse:
        if request.query_params:
            data = request.query_params
        else:
            try:
                data = await request.json()
            except JSONDecodeError:
                data = {}
        apidata = ApiData(data, self)
        try:
            response = await self.api(apidata)
        except NotFoundError as e:
            return api_error(e, code=404)
        except ForbiddenError as e:
            return api_error(e, code=403)
        except NotImplementedError as e:
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

    async def api(self, data: ApiData) -> ru.JSON:
        raise NotImplementedError()

    @classmethod
    def swagger(cls) -> ru.JSON:
        """Generate one or more swagger paths for this ApiStar."""
        result = {}
        for method in cls.methods:
            result[method.lower()] = {
                "operationId": cls.__name__,
                "summary": cls.summary,
                "description": cls.description,
                "responses": {
                    "200": {"description": "Success"},
                    "400": {"description": "Bad request"},
                    "403": {"description": "Forbidden"},
                    "404": {"description": "Not found"},
                    "500": {"description": "Serverside unhandled exception"},
                    "501": {"description": "Not yet implemented"}
                },
                "tags": cls.tags,
                "parameters": [{
                    "name": parameter,
                    "in": "query",
                    "description": cls.parameters[parameter],
                    "type": "string"
                } for parameter in cls.parameters]
            }
            if cls.requires_auth:
                result[method.lower()]["security"] = [{"RoyalnetLoginToken": ["logged_in"]}]
        return result
