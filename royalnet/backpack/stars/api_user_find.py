import royalnet.utils as ru
import royalnet.backpack.tables as rbt
import royalnet.constellation.api as rca


class ApiUserFindStar(rca.ApiStar):
    path = "/api/user/find/v1"

    parameters = {
        "get": {
            "alias": "One of the aliases of the user to get."
        }
    }

    @rca.magic
    async def get(self, data: rca.ApiData) -> ru.JSON:
        """Get details about the Royalnet user with a certain alias."""
        user = await rbt.User.find(self.alchemy, data.session, data["alias"])
        if user is None:
            raise rca.NotFoundError("No such user.")
        return user.json()
