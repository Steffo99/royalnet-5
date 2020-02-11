from typing import *
import datetime
import royalnet.utils as ru
from royalnet.constellation.api import *
from ..tables.tokens import Token


class ApiTokenCreateStar(ApiStar):
    path = "/api/token/create/v1"

    methods = ["POST"]

    async def api(self, data: ApiData) -> ru.JSON:
        user = await data.user()
        try:
            duration = int(data["duration"])
        except ValueError:
            raise InvalidParameterError("Duration is not a valid integer")
        new_token = Token.generate(self.alchemy, user, datetime.timedelta(seconds=duration))
        data.session.add(new_token)
        await data.session_commit()
        return new_token.json()
