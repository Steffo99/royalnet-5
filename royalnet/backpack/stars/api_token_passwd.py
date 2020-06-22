from typing import *
import datetime
import royalnet.utils as ru
from royalnet.constellation.api import *
from sqlalchemy import and_
from ..tables.tokens import Token


class ApiTokenPasswdStar(ApiStar):
    path = "/api/token/passwd/v1"

    methods = ["PUT"]

    tags = ["token"]

    parameters = {
        "put": {
            "new_password": "The password you want to set."
        }
    }

    requires_auth = True

    async def put(self, data: ApiData) -> ru.JSON:
        """Change the password of the currently logged in user."""
        TokenT = self.alchemy.get(Token)
        token = await data.token()
        user = token.user
        user.set_password(data["new_password"])
        tokens: List[Token] = await ru.asyncify(
            data.session
                .query(self.alchemy.get(Token))
                .filter(
                    and_(
                        TokenT.user == user,
                        TokenT.expiration >= datetime.datetime.now()
                    ))
                .all
        )
        for t in tokens:
            if t.token != token.token:
                t.expired = True
        await data.session_commit()
        return {
            "revoked_tokens": len(tokens) - 1
        }
