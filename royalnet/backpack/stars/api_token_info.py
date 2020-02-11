import royalnet.utils as ru
from royalnet.constellation.api import *


class ApiTokenInfoStar(ApiStar):
    path = "/api/token/info/v1"

    async def api(self, data: ApiData) -> ru.JSON:
        token = await data.token()
        return token.json()
