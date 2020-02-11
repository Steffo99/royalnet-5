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
