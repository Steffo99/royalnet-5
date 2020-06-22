from royalnet.utils import *
from royalnet.backpack.tables import *
from royalnet.constellation.api import *


class ApiUserGetStar(ApiStar):
    path = "/api/user/get/v1"

    parameters = {
        "get": {
            "id": "The id of the user to get."
        }
    }

    tags = ["user"]

    async def get(self, data: ApiData) -> dict:
        """Get details about the Royalnet user with a certain id."""
        user_id_str = data["id"]
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise InvalidParameterError("'id' is not a valid int.")
        user: User = await asyncify(data.session.query(self.alchemy.get(User)).get, user_id)
        if user is None:
            raise NotFoundError("No such user.")
        return user.json()
