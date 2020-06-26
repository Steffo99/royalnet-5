from starlette.responses import *
import royalnet.utils as ru
import royalnet.backpack.tables as rbt
import royalnet.constellation.api as rca


class ApiUserListStar(rca.ApiStar):
    path = "/api/user/list/v1"

    tags = ["user"]

    @rca.magic
    async def get(self, data: rca.ApiData) -> ru.JSON:
        """Get a list of all Royalnet users."""
        users: typing.List[rbt.User] = await ru.asyncify(data.session.query(self.alchemy.get(rbt.User)).all)
        return [user.json() for user in users]
