import royalnet.utils as ru
import royalnet.backpack.tables as rbt
import royalnet.constellation.api as rca


class ApiUserGetStar(rca.ApiStar):
    path = "/api/user/get/v1"

    parameters = {
        "get": {
            "id": "The id of the user to get."
        }
    }

    tags = ["user"]

    @rca.magic
    async def get(self, data: rca.ApiData) -> dict:
        """Get details about the Royalnet user with a certain id."""
        user_id_str = data["id"]
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise rca.InvalidParameterError("'id' is not a valid int.")
        user: rbt.User = await ru.asyncify(data.session.query(self.alchemy.get(rbt.User)).get, user_id)
        if user is None:
            raise rca.NotFoundError("No such user.")
        return user.json()
