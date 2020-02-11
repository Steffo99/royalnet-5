import royalnet.version as rv
from royalnet.constellation.api import *
import royalnet.utils as ru


class ApiRoyalnetVersionStar(ApiStar):
    path = "/api/royalnet/version/v1"

    async def api(self, data: ApiData) -> ru.JSON:
        return {
            "semantic": rv.semantic
        }
