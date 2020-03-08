import royalnet.utils as ru
from royalnet.constellation.api import *
from royalnet.version import semantic


class ApiDocsStar(ApiStar):
    path = "/api/docs"

    async def api(self, data: ApiData) -> ru.JSON:
        return
