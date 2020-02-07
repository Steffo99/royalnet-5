import datetime
import royalnet.utils as ru
from royalnet.constellation.api import *
from ..tables.users import User
from ..tables.aliases import Alias


class ApiTokenInfoStar(ApiStar):
    path = "/api/token/info/v1"

    async def api(self, data: ApiData) -> dict:
        token = await data.token()
        return token.json()
