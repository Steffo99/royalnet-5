import royalnet.utils as ru
from royalnet.constellation.api import *


class ApiTokenInfoStar(ApiStar):
    path = "/api/token/info/v1"

    summary = "Get info about a login token."

    parameters = {
        "token": "The login token to get info about.",
    }

    async def api(self, data: ApiData) -> ru.JSON:
        token = await data.token()
        return token.json()
