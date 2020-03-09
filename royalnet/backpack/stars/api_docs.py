import royalnet.utils as ru
from royalnet.constellation.api import *
from royalnet.version import semantic


class ApiDocsStar(ApiStar):
    path = "/api/docs"

    summary = "Get the swagger.json file used to generate this documentation."

    async def api(self, data: ApiData) -> ru.JSON:
        return
