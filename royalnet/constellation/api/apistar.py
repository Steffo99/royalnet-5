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
    def swagger(cls) -> str:
        """Generate one or more swagger paths for this ApiStar."""
        string = [f'{cls.path}:\n']
        for method in cls.methods:
            string.append(
                f'    {method.lower()}:\n'
                f'      summary: "{cls.summary}"\n'
                f'      description: "{cls.description}"\n'
                f'      produces:\n'
                f'      - "application/json"\n'
                f'      responses:\n'
                f'        200:\n'
                f'          description: "Success"\n'
                f'        400:\n'
                f'          description: "Bad request"\n'
                f'        403:\n'
                f'          description: "Forbidden"\n'
                f'        404:\n'
                f'          description: "Not found"\n'
                f'        500:\n'
                f'          description: "Serverside unhandled exception"\n'
                f'        501:\n'
                f'          description: "Not yet implemented"\n'
            )
            if len(cls.parameters) > 0:
                string.append(f'      parameters:\n')
            for parameter in cls.parameters:
                string.append(
                    f'        - name: "{parameter}"\n'
                    f'          in: "query"\n'
                    f'          description: "{cls.parameters[parameter]}"\n'
                    f'          type: "string"\n'
                )
        return "".join(string).rstrip("\n")
