from starlette.responses import *
from royalnet.utils import *
from royalnet.backpack.tables import *
from royalnet.constellation.api import *


class ApiAliasListStar(ApiStar):
    path = "/api/alias/list/v1"

    summary = "Get all aliases of the specified user."

    tags = ["alias"]

    parameters = {
        "user_id": "The id of the user to get the aliases of."
    }

    async def api(self, data: ApiData) -> JSON:
        aliases: typing.List[Alias] = await asyncify(
            data.session
                .query(self.alchemy.get(Alias))
                .filter_by(user_id=data["user_id"])
                .all
        )
        return [alias.alias for alias in aliases]
