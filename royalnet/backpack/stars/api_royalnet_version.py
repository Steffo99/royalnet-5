import royalnet.version as rv
import royalnet.constellation.api as rca
import royalnet.utils as ru


class ApiRoyalnetVersionStar(rca.ApiStar):
    path = "/api/royalnet/version/v1"

    tags = ["royalnet"]

    @rca.magic
    async def get(self, data: rca.ApiData) -> ru.JSON:
        """Get the current Royalnet version."""
        return {
            "semantic": rv.semantic
        }
