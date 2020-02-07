import royalnet.version as rv
from royalnet.constellation.api import *


class ApiRoyalnetVersionStar(ApiStar):
    path = "/api/royalnet/version/v1"

    async def api(self, data: ApiData) -> dict:
        return {
            "semantic": rv.semantic
        }
