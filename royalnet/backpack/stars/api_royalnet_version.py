import royalnet.version as rv
from royalnet.constellation import ApiStar


class ApiRoyalnetVersionStar(ApiStar):
    path = "/api/royalnet/version"

    async def api(self, data: dict) -> dict:
        return {
            "semantic": rv.semantic
        }
