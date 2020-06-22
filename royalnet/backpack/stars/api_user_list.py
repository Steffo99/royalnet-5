from starlette.responses import *
from royalnet.utils import *
from royalnet.backpack.tables import *
from royalnet.constellation.api import *


class ApiUserListStar(ApiStar):
    path = "/api/user/list/v1"

    tags = ["user"]

    async def get(self, data: ApiData) -> JSON:
        "Get a list of all Royalnet users."
        users: typing.List[User] = await asyncify(data.session.query(self.alchemy.get(User)).all)
        return [user.json() for user in users]
