from royalnet.utils import *
from royalnet.backpack.tables import *
from royalnet.constellation.api import *


class ApiUserGetStar(ApiStar):
    path = "/api/user/get/v1"

    summary = "Get a Royalnet user by its id."

    parameters = {
        "id": "The id of the user to get."
    }

    tags = ["user"]

    async def api(self, data: ApiData) -> dict:
        user_id_str = data["id"]
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise InvalidParameterError("'id' is not a valid int.")
        user: User = await asyncify(data.session.query(self.alchemy.get(User)).get, user_id)
        if user is None:
            raise NotFoundError("No such user.")
        return user.json()
