from royalnet.utils import *
from royalnet.backpack.tables import *
from royalnet.constellation.api import *


class ApiUserFindStar(ApiStar):
    path = "/api/user/find/v1"

    summary = "Find a Royalnet user by one of their aliases."

    tags = ["user"]

    parameters = {
        "alias": "One of the aliases of the user to get."
    }

    async def api(self, data: ApiData) -> dict:
        user = await User.find(self.alchemy, data.session, data["alias"])
        if user is None:
            raise NotFoundError("No such user.")
        return user.json()
