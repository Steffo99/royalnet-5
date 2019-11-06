from starlette.requests import Request
from starlette.responses import *
from royalnet.web import *
from royalnet.utils import *
from royalnet.packs.common.tables import User


class ApiUserGetStar(PageStar):
    path = "/api/user/get/{uid_str}"
    tables = {User}

    async def page(self, request: Request) -> JSONResponse:
        uid_str = request.path_params.get("uid_str", "")
        try:
            uid = int(uid_str)
        except (ValueError, TypeError):
            return error(400, "Invalid uid")
        async with self.alchemy.session_acm() as session:
            user: User = await asyncify(session.query(self.alchemy.User).get, uid)
        if user is None:
            return error(404, "No such user")
        return JSONResponse(user.json())
