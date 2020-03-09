import royalnet.utils as ru
from royalnet.constellation.api import *


class ApiTokenInfoStar(ApiStar):
    path = "/api/token/info/v1"

    summary = "Get info the current login token."

    tags = ["token"]

    requires_auth = True

    async def api(self, data: ApiData) -> ru.JSON:
        token = await data.token()
        return token.json()
