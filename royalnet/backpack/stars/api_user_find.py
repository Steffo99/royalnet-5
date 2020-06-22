from royalnet.utils import *
from royalnet.backpack.tables import *
from royalnet.constellation.api import *


class ApiUserFindStar(ApiStar):
    path = "/api/user/find/v1"

    tags = ["user"]

    parameters = {
        "get": {
            "alias": "One of the aliases of the user to get."
        }
    }

    async def get(self, data: ApiData) -> dict:
        """Get details about the Royalnet user with a certain alias."""
        user = await User.find(self.alchemy, data.session, data["alias"])
        if user is None:
            raise NotFoundError("No such user.")
        return user.json()
