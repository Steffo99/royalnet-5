import royalnet.utils as ru
from royalnet.constellation.api import *


class ApiTokenInfoStar(ApiStar):
    path = "/api/token/info/v1"

    tags = ["login"]

    async def get(self, data: ApiData) -> ru.JSON:
        """Get information about the current login token."""
        token = await data.token()
        return token.json()
