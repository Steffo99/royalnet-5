import royalnet.version as rv
from royalnet.constellation.api import *
import royalnet.utils as ru


class ApiRoyalnetVersionStar(ApiStar):
    path = "/api/royalnet/version/v1"

    methods = ["GET"]

    tags = ["royalnet"]

    async def get(self, data: ApiData) -> ru.JSON:
        """Get the current Royalnet version."""
        return {
            "semantic": rv.semantic
        }
